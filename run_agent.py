#!/usr/bin/env python3
"""
Agent evaluation: Claude Code running programmatically (headless mode).
Runs separately on each dataset. Saves full reasoning logs.
"""

import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from dotenv import dotenv_values

# Load environment variables from .env file
env_file = Path(__file__).parent / ".env"
env_vars = dotenv_values(env_file)
for key, value in env_vars.items():
    if value:
        os.environ[key] = value

# Configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
RESULTS_DIR = Path(__file__).parent / "results" / "agent"
SYMPTOMS_FILE = Path(__file__).parent / "disease_symptoms.md"
PROJECT_DIR = Path(__file__).parent


def get_available_datasets():
    """Get list of available datasets in test_data directory."""
    datasets = []
    for item in TEST_DATA_DIR.iterdir():
        if item.is_dir() and (item / "ground_truth.json").exists():
            datasets.append(item.name)
    return sorted(datasets)


def load_dataset(dataset_name: str):
    """Load test images and expected classes for a specific dataset."""
    dataset_dir = TEST_DATA_DIR / dataset_name
    ground_truth_file = dataset_dir / "ground_truth.json"

    if not ground_truth_file.exists():
        raise FileNotFoundError(f"Ground truth not found: {ground_truth_file}")

    with open(ground_truth_file, 'r') as f:
        data = json.load(f)

    expected_classes = data["expected_classes"]
    description = data.get("description", dataset_name)
    images = []

    for img_name, info in data["images"].items():
        images.append({
            "name": img_name,
            "path": str(dataset_dir / "images" / img_name),
            "ground_truth": info["label"]
        })

    return images, expected_classes, description


def extract_prediction_from_result(result_text: str) -> str:
    """Extract prediction from the result text."""
    # Try to find JSON in the result
    json_match = re.search(r'\{[^}]*"prediction"[^}]*\}', result_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return parsed.get("prediction", "UNKNOWN")
        except:
            pass
    return "UNKNOWN"


def classify_with_agent(image_path: str, expected_classes: list, dataset_description: str) -> dict:
    """
    Classify image using Claude Code in headless mode.
    Returns full output including reasoning.
    """

    abs_image_path = str(Path(image_path).resolve())
    abs_symptoms_path = str(SYMPTOMS_FILE.resolve())

    prompt = f"""You are a plant disease classification agent.

DATASET: {dataset_description}
AVAILABLE CLASSES: {expected_classes}

TASK: Classify the disease/condition in the image at: {abs_image_path}

INSTRUCTIONS:
1. Read the knowledge base at {abs_symptoms_path} - focus on the section relevant to this dataset
2. View the target image at {abs_image_path}
3. Compare visual features to the symptom descriptions
4. You MUST view reference images for your top 2-3 candidate classes using the EXACT paths listed in the knowledge base (they are relative to {str(PROJECT_DIR)})
5. Make your prediction from the available classes only

OUTPUT: After your analysis, return a JSON object:
{{"prediction": "class_name"}}

The prediction must be exactly one of: {expected_classes}"""

    try:
        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--allowedTools", "Read",
                "--output-format", "stream-json",
                "--verbose",
                "--model", "haiku"
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_DIR),
            timeout=180  # 3 minute timeout
        )

        if result.returncode != 0:
            return {
                "prediction": "ERROR",
                "reasoning": "",
                "error": result.stderr,
                "raw_output": result.stdout,
                "success": False
            }

        # Parse NDJSON lines to extract full reasoning trace
        trace = []
        final_result = {}
        for line in result.stdout.strip().split('\n'):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "assistant":
                for c in obj.get("message", {}).get("content", []):
                    if c.get("type") == "text" and c.get("text", "").strip():
                        trace.append({"role": "assistant", "type": "text", "content": c["text"].strip()})
                    elif c.get("type") == "tool_use":
                        trace.append({"role": "assistant", "type": "tool_use", "tool": c["name"], "input": c.get("input", {})})
            elif obj.get("type") == "result":
                final_result = obj

        # The final assistant text is the reasoning + prediction
        reasoning = final_result.get("result", "")
        prediction = extract_prediction_from_result(reasoning)

        return {
            "prediction": prediction,
            "reasoning": reasoning,
            "trace": trace,
            "session_id": final_result.get("session_id"),
            "duration_ms": final_result.get("duration_ms"),
            "num_turns": final_result.get("num_turns"),
            "cost_usd": final_result.get("total_cost_usd"),
            "success": True
        }

    except subprocess.TimeoutExpired:
        return {"prediction": "TIMEOUT", "reasoning": "", "trace": [], "success": False}
    except Exception as e:
        return {"prediction": "ERROR", "reasoning": "", "trace": [], "error": str(e), "success": False}


def run_agent_on_dataset(dataset_name: str, logs_dir: Path, limit: int = None) -> float:
    """Run agent evaluation on a single dataset."""

    print(f"\n{'='*60}")
    print(f"AGENT: {dataset_name}")
    print(f"{'='*60}")

    # Load dataset
    test_images, expected_classes, description = load_dataset(dataset_name)
    if limit:
        test_images = test_images[:limit]

    print(f"Description: {description}")
    print(f"Classes ({len(expected_classes)}): {expected_classes}")
    print(f"Test Images: {len(test_images)}")

    # Create logs directory for this dataset
    dataset_logs_dir = logs_dir / dataset_name
    dataset_logs_dir.mkdir(parents=True, exist_ok=True)

    # Results storage
    correct = 0

    print("\nProcessing images (Claude Code agent)...")
    for i, img_info in enumerate(test_images):
        image_path = img_info["path"]
        image_name = img_info["name"]
        ground_truth = img_info["ground_truth"]

        print(f"\n  [{i+1}/{len(test_images)}] {image_name} (ground truth: {ground_truth})")
        print(f"  Processing...", end=" ", flush=True)

        classification = classify_with_agent(image_path, expected_classes, description)
        prediction = classification["prediction"]
        is_correct = prediction == ground_truth

        if is_correct:
            correct += 1

        # Save individual log (the only output per image)
        log_entry = {
            "image_name": image_name,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "correct": is_correct,
            "reasoning": classification.get("reasoning", ""),
            "trace": classification.get("trace", []),
            "duration_ms": classification.get("duration_ms"),
            "num_turns": classification.get("num_turns"),
            "cost_usd": classification.get("cost_usd"),
            "session_id": classification.get("session_id")
        }

        log_file = dataset_logs_dir / f"{image_name.replace('.jpg', '')}_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2)

        status = "OK" if is_correct else f"WRONG (predicted: {prediction})"
        print(status)

        # Show brief reasoning
        reasoning = classification.get("reasoning", "")
        if reasoning:
            preview = reasoning[:200].replace('\n', ' ')
            print(f"  Reasoning: {preview}...")

    # Calculate accuracy
    accuracy = (correct / len(test_images)) * 100 if test_images else 0

    print(f"\n  Results: {correct}/{len(test_images)} correct ({accuracy:.1f}%)")
    print(f"  Logs: {dataset_logs_dir}/")

    return accuracy


def run_agent(dataset_filter=None, limit=None):
    """Run agent evaluation.

    Args:
        dataset_filter: Run only this dataset (e.g. 'Foliar_Disease_Stress')
        limit: Max number of images per dataset (e.g. 2)
    """

    print("=" * 60)
    print("AGENT EVALUATION (Claude Code Headless, Per Dataset)")
    print("=" * 60)

    # Check prerequisites
    if not TEST_DATA_DIR.exists():
        print(f"\nERROR: Test data not found: {TEST_DATA_DIR}")
        print("Run 'python prepare_test_data.py' first.")
        return

    if not SYMPTOMS_FILE.exists():
        print(f"\nERROR: Symptoms file not found: {SYMPTOMS_FILE}")
        print("Run 'python generate_symptoms.py' first.")
        return

    datasets = get_available_datasets()
    if dataset_filter:
        datasets = [d for d in datasets if d == dataset_filter]
    if not datasets:
        print(f"\nERROR: No datasets found in {TEST_DATA_DIR}")
        return

    print(f"\nDatasets: {datasets}")
    if limit:
        print(f"Limit: {limit} images per dataset")
    print(f"Knowledge base: {SYMPTOMS_FILE}")

    # Create results and logs directories
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logs_dir = RESULTS_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Run on each dataset
    all_results = {}
    for dataset_name in datasets:
        accuracy = run_agent_on_dataset(dataset_name, logs_dir, limit=limit)
        all_results[dataset_name] = accuracy

    # Print summary
    print("\n" + "=" * 60)
    print("AGENT SUMMARY")
    print("=" * 60)
    for dataset_name, accuracy in all_results.items():
        print(f"  {dataset_name}: {accuracy:.1f}%")

    print(f"\nFull logs saved to: {logs_dir}/")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, help="Run only this dataset")
    parser.add_argument("--limit", type=int, help="Max images per dataset")
    args = parser.parse_args()
    run_agent(dataset_filter=args.dataset, limit=args.limit)

    # Examples to run:
#   - python run_agent.py --dataset Foliar_Disease_Stress --limit 1                                                                                                                                          
#   - python run_agent.py --dataset Foliar_Disease_Stress --limit 3
#   - python run_agent.py --dataset Disease_Severity --limit 2                                                                                                                                               
#   - python run_agent.py (runs everything)