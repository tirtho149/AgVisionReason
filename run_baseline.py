#!/usr/bin/env python3
"""
Baseline evaluation: Direct Claude Haiku API inference without symptoms knowledge.
Runs separately on each dataset (Foliar_Disease_Stress, Disease_Severity).
"""

import os
import re
import json
import base64
import csv
from pathlib import Path
from datetime import datetime
from dotenv import dotenv_values
import anthropic

# Load environment variables from .env file
env_file = Path(__file__).parent / ".env"
env_vars = dotenv_values(env_file)
for key, value in env_vars.items():
    if value:
        os.environ[key] = value

# Configuration
MODEL = "claude-haiku-4-5-20251001"
TEST_DATA_DIR = Path(__file__).parent / "test_data"
RESULTS_DIR = Path(__file__).parent / "results" / "baseline"


def load_image_base64(image_path: str) -> str:
    """Load image and convert to base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_media_type(image_path: str) -> str:
    """Get media type from image extension."""
    ext = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    return media_types.get(ext, "image/jpeg")


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


def extract_json(response_text: str) -> dict:
    """Extract JSON from response text."""
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {}


def classify_image(client: anthropic.Anthropic, image_path: str, expected_classes: list) -> dict:
    """Classify a single image using baseline prompt (no symptoms)."""

    prompt = f"""Given the image, identify the class. Use the following list of possible classes for your prediction. It should be one of the: {expected_classes}. Be attentive to subtle details as some classes may appear similar.

Provide your answer in the following JSON format:
{{"prediction": "class_name"}}

Replace "class_name" with the appropriate class from the list above based on your analysis of the image.
The labels should be entered exactly as they are in the list above i.e., {expected_classes}.
The response should start with {{ and contain only a JSON object (as specified above) and no other text."""

    image_base64 = load_image_base64(image_path)
    media_type = get_media_type(image_path)

    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    response_text = message.content[0].text
    result = extract_json(response_text)

    return {
        "prediction": result.get("prediction", "UNKNOWN"),
        "raw_response": response_text
    }


def run_baseline_on_dataset(client: anthropic.Anthropic, dataset_name: str) -> tuple:
    """Run baseline evaluation on a single dataset."""

    print(f"\n{'='*60}")
    print(f"BASELINE: {dataset_name}")
    print(f"{'='*60}")

    # Load dataset
    test_images, expected_classes, description = load_dataset(dataset_name)

    print(f"Description: {description}")
    print(f"Classes ({len(expected_classes)}): {expected_classes}")
    print(f"Test Images: {len(test_images)}")

    # Results storage
    results = []
    correct = 0

    print("\nProcessing images...")
    for i, img_info in enumerate(test_images):
        image_path = img_info["path"]
        image_name = img_info["name"]
        ground_truth = img_info["ground_truth"]

        print(f"  [{i+1}/{len(test_images)}] {image_name}...", end=" ", flush=True)

        try:
            classification = classify_image(client, image_path, expected_classes)
            prediction = classification["prediction"]
            is_correct = prediction == ground_truth

            if is_correct:
                correct += 1

            results.append({
                "image_name": image_name,
                "ground_truth": ground_truth,
                "prediction": prediction,
                "correct": is_correct
            })

            status = "OK" if is_correct else f"WRONG (predicted: {prediction})"
            print(status)

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "image_name": image_name,
                "ground_truth": ground_truth,
                "prediction": "ERROR",
                "correct": False
            })

    # Calculate accuracy
    accuracy = (correct / len(test_images)) * 100 if test_images else 0

    # Save results
    output_file = RESULTS_DIR / f"{dataset_name}_predictions.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "ground_truth", "prediction", "correct"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults: {correct}/{len(test_images)} correct ({accuracy:.1f}%)")
    print(f"Saved to: {output_file}")

    return results, accuracy


def run_baseline():
    """Run baseline evaluation on all datasets."""

    print("=" * 60)
    print("BASELINE EVALUATION (Per Dataset)")
    print(f"Model: {MODEL}")
    print("=" * 60)

    # Check for test data
    if not TEST_DATA_DIR.exists():
        print(f"\nERROR: Test data not found: {TEST_DATA_DIR}")
        print("Run 'python prepare_test_data.py' first.")
        return

    datasets = get_available_datasets()
    if not datasets:
        print(f"\nERROR: No datasets found in {TEST_DATA_DIR}")
        return

    print(f"\nDatasets found: {datasets}")

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Setup client
    client = anthropic.Anthropic()

    # Run on each dataset
    all_results = {}
    for dataset_name in datasets:
        results, accuracy = run_baseline_on_dataset(client, dataset_name)
        all_results[dataset_name] = {"results": results, "accuracy": accuracy}

    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE SUMMARY")
    print("=" * 60)
    for dataset_name, data in all_results.items():
        print(f"  {dataset_name}: {data['accuracy']:.1f}%")

    return all_results


if __name__ == "__main__":
    run_baseline()
