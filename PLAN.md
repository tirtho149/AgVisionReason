# Plant Disease Classification - Baseline vs Agent Comparison

## Goal
Compare two approaches using Claude Haiku:
1. **Baseline**: Direct API inference (no symptoms knowledge)
2. **Agent**: Claude Code running programmatically (headless mode) with agentic access to symptoms + images

---

## Key Changes from Previous Plan

1. **Data Isolation**: Create anonymized test set to prevent label leakage
2. **True Agent**: Use `claude -p` (Claude Code headless) instead of API calls

---

## Project Structure

```
reasoning/
├── Plant_Disease_Dataset/          # Source data (120 images, labeled folders)
├── test_data/                      # NEW: Anonymized test subset
│   ├── images/                     # Images with random IDs (test_001.jpg, etc.)
│   └── ground_truth.json           # Hidden labels for validation only
├── disease_symptoms.md             # Knowledge base (already generated)
├── generate_symptoms.py            # GPT API script (already done)
├── prepare_test_data.py            # NEW: Creates anonymized test set
├── run_baseline.py                 # UPDATED: Uses test_data/
├── run_agent.py                    # NEW: Uses claude -p (headless mode)
├── evaluate.py                     # Compare results
└── results/
    ├── baseline/predictions.csv
    └── agent/predictions.csv
```

---

## Step 1: Prepare Anonymized Test Data

### `prepare_test_data.py`

Creates a clean test set where labels are hidden:

```python
# What it does:
# 1. Sample N images from Plant_Disease_Dataset
# 2. Copy to test_data/images/ with random names (test_001.jpg, test_002.jpg...)
# 3. Store ground truth in test_data/ground_truth.json (hidden from model)

# Output structure:
test_data/
├── images/
│   ├── test_001.jpg
│   ├── test_002.jpg
│   └── ...
└── ground_truth.json  # {"test_001.jpg": "Anthracnose", "test_002.jpg": "Die_Back", ...}
```

This ensures:
- Model can't infer labels from file paths
- Same test set used for both baseline and agent (fair comparison)

---

## Step 2: Baseline (API Call)

### `run_baseline.py` (Updated)

Direct Claude Haiku API call - no agentic behavior:

```python
# For each image in test_data/images/:
#   1. Load image as base64
#   2. Send to Claude Haiku with baseline prompt
#   3. Get prediction
#   4. Save to results/baseline/predictions.csv

# Baseline prompt:
"""
Given the image, identify the class from: {expected_classes}
Provide answer as JSON: {"prediction": "class_name"}
"""
```

Model: `claude-haiku-4-5-20251001`

---

## Step 3: Agent (Claude Code Headless)

### `run_agent.py` (New Approach)

Uses `claude -p` to run Claude Code programmatically:

```python
import subprocess
import json

# For each image in test_data/images/:
#   1. Invoke claude -p with agentic prompt
#   2. Claude Code can: read symptoms, view image, reason, decide
#   3. Parse structured output
#   4. Save to results/agent/predictions.csv

def classify_with_agent(image_path: str) -> str:
    prompt = f"""
    You are a plant disease classification agent.

    TASK: Classify the disease in this image: {image_path}

    INSTRUCTIONS:
    1. First, read the knowledge base at disease_symptoms.md
    2. View the target image
    3. Compare visual features to symptom descriptions
    4. If uncertain, view reference images listed in the knowledge base
    5. Make your prediction

    Return ONLY a JSON object: {{"prediction": "class_name"}}
    """

    result = subprocess.run([
        "claude", "-p", prompt,
        "--allowedTools", "Read",
        "--output-format", "json",
        "--json-schema", '{"type":"object","properties":{"prediction":{"type":"string"}},"required":["prediction"]}',
        "--model", "haiku"
    ], capture_output=True, text=True)

    output = json.loads(result.stdout)
    return output["structured_output"]["prediction"]
```

Key difference: Claude Code operates agentically:
- Uses Read tool to load symptoms
- Uses Read tool to view images
- Makes multi-step decisions
- Can dynamically look at reference images if needed

---

## Step 4: Evaluate

### `evaluate.py`

Compares baseline vs agent:

```python
# Load predictions from both approaches
# Load ground_truth.json
# Calculate:
#   - Overall accuracy
#   - Per-class accuracy
#   - Improvement delta
# Generate report
```

---

## Execution Flow

```bash
# 1. Prepare anonymized test data (24 images = 2 per class × 12 classes)
python prepare_test_data.py --per-class 2

# 2. Run baseline
python run_baseline.py

# 3. Run agent (uses claude -p)
python run_agent.py

# 4. Evaluate
python evaluate.py
```

---

## Files to Create/Update

| File | Status | Description |
|------|--------|-------------|
| `prepare_test_data.py` | NEW | Creates anonymized test set |
| `run_baseline.py` | UPDATE | Use test_data/, keep API approach |
| `run_agent.py` | REWRITE | Use `claude -p` headless mode |
| `evaluate.py` | UPDATE | Read from ground_truth.json |

---

## Why This Approach

1. **No label contamination**: Test images have random IDs, labels in separate file
2. **True agentic behavior**: Claude Code can read files, view images, make decisions
3. **Fair comparison**: Same test set, same model (Haiku), different reasoning approaches
4. **Reproducible**: Structured JSON output with schema validation
