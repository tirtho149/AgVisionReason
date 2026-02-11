#!/usr/bin/env python3
"""
Evaluate and compare baseline vs agent results.
Shows results per dataset (Foliar_Disease_Stress, Disease_Severity).
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
PROJECT_DIR = Path(__file__).parent
RESULTS_DIR = PROJECT_DIR / "results"
TEST_DATA_DIR = PROJECT_DIR / "test_data"


def get_available_datasets():
    """Get list of datasets from test_data directory."""
    datasets = []
    for item in TEST_DATA_DIR.iterdir():
        if item.is_dir() and (item / "ground_truth.json").exists():
            datasets.append(item.name)
    return sorted(datasets)


def load_ground_truth(dataset_name: str):
    """Load ground truth for a specific dataset."""
    gt_file = TEST_DATA_DIR / dataset_name / "ground_truth.json"
    if not gt_file.exists():
        return {}, []

    with open(gt_file, 'r') as f:
        data = json.load(f)

    return data.get("images", {}), data.get("expected_classes", [])


def load_results(filepath: Path) -> list:
    """Load results from CSV file."""
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def calculate_metrics(results: list, expected_classes: list) -> dict:
    """Calculate accuracy metrics from results."""
    if not results:
        return {"total": 0, "correct": 0, "accuracy": 0.0, "per_class": {}}

    total = len(results)
    correct = sum(1 for r in results if r["correct"] == "True" or r["correct"] is True)
    accuracy = (correct / total) * 100 if total > 0 else 0.0

    # Per-class accuracy
    class_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        gt = r["ground_truth"]
        class_stats[gt]["total"] += 1
        if r["correct"] == "True" or r["correct"] is True:
            class_stats[gt]["correct"] += 1

    per_class = {}
    for cls in expected_classes:
        stats = class_stats.get(cls, {"correct": 0, "total": 0})
        per_class[cls] = {
            "correct": stats["correct"],
            "total": stats["total"],
            "accuracy": (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0.0
        }

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_class": per_class
    }


def print_dataset_comparison(dataset_name: str, baseline_metrics: dict, agent_metrics: dict, expected_classes: list):
    """Print comparison for a single dataset."""

    print(f"\n{'='*70}")
    print(f"  {dataset_name}")
    print(f"{'='*70}")

    b_acc = baseline_metrics["accuracy"]
    a_acc = agent_metrics["accuracy"]
    diff = a_acc - b_acc

    print(f"\n{'Approach':<25} {'Correct':<12} {'Total':<10} {'Accuracy':<12}")
    print("-" * 60)
    print(f"{'Baseline (API)':<25} {baseline_metrics['correct']:<12} {baseline_metrics['total']:<10} {b_acc:.1f}%")
    print(f"{'Agent (Claude Code)':<25} {agent_metrics['correct']:<12} {agent_metrics['total']:<10} {a_acc:.1f}%")
    print("-" * 60)

    if diff > 0:
        print(f"{'IMPROVEMENT:':<25} +{diff:.1f}%")
    elif diff < 0:
        print(f"{'DIFFERENCE:':<25} {diff:.1f}%")
    else:
        print(f"{'DIFFERENCE:':<25} 0%")

    # Per-class breakdown
    print(f"\nPer-Class Breakdown:")
    print(f"{'Class':<30} {'Baseline':<12} {'Agent':<12} {'Diff':<10}")
    print("-" * 65)

    for cls in expected_classes:
        b_cls = baseline_metrics["per_class"].get(cls, {"correct": 0, "total": 0, "accuracy": 0})
        a_cls = agent_metrics["per_class"].get(cls, {"correct": 0, "total": 0, "accuracy": 0})
        cls_diff = a_cls["accuracy"] - b_cls["accuracy"]

        b_str = f"{b_cls['correct']}/{b_cls['total']}" if b_cls['total'] > 0 else "N/A"
        a_str = f"{a_cls['correct']}/{a_cls['total']}" if a_cls['total'] > 0 else "N/A"
        diff_str = f"+{cls_diff:.0f}%" if cls_diff > 0 else f"{cls_diff:.0f}%"

        print(f"{cls:<30} {b_str:<12} {a_str:<12} {diff_str}")


def generate_report(all_metrics: dict) -> str:
    """Generate markdown evaluation report."""

    report = f"""# Evaluation Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overall Summary

| Dataset | Baseline | Agent | Improvement |
|---------|----------|-------|-------------|
"""

    for dataset_name, data in all_metrics.items():
        b_acc = data["baseline"]["accuracy"]
        a_acc = data["agent"]["accuracy"]
        diff = a_acc - b_acc
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"
        report += f"| {dataset_name} | {b_acc:.1f}% | {a_acc:.1f}% | {diff_str} |\n"

    for dataset_name, data in all_metrics.items():
        report += f"""
---

## {dataset_name}

### Summary
- **Baseline**: {data['baseline']['correct']}/{data['baseline']['total']} ({data['baseline']['accuracy']:.1f}%)
- **Agent**: {data['agent']['correct']}/{data['agent']['total']} ({data['agent']['accuracy']:.1f}%)

### Per-Class Results

| Class | Baseline | Agent | Diff |
|-------|----------|-------|------|
"""
        for cls in data["expected_classes"]:
            b_cls = data["baseline"]["per_class"].get(cls, {"correct": 0, "total": 0, "accuracy": 0})
            a_cls = data["agent"]["per_class"].get(cls, {"correct": 0, "total": 0, "accuracy": 0})
            cls_diff = a_cls["accuracy"] - b_cls["accuracy"]

            b_str = f"{b_cls['correct']}/{b_cls['total']}"
            a_str = f"{a_cls['correct']}/{a_cls['total']}"
            diff_str = f"+{cls_diff:.0f}%" if cls_diff > 0 else f"{cls_diff:.0f}%"

            report += f"| {cls} | {b_str} | {a_str} | {diff_str} |\n"

    return report


def evaluate():
    """Run evaluation and comparison per dataset."""

    print("=" * 70)
    print("EVALUATION: BASELINE vs AGENT (Per Dataset)")
    print("=" * 70)

    # Get available datasets
    datasets = get_available_datasets()
    if not datasets:
        print(f"\nNo datasets found in {TEST_DATA_DIR}")
        print("Run 'python prepare_test_data.py' first.")
        return

    print(f"\nDatasets: {datasets}")

    all_metrics = {}

    for dataset_name in datasets:
        # Load ground truth
        _, expected_classes = load_ground_truth(dataset_name)

        # Load results
        baseline_file = RESULTS_DIR / "baseline" / f"{dataset_name}_predictions.csv"
        agent_file = RESULTS_DIR / "agent" / f"{dataset_name}_predictions.csv"

        baseline_results = load_results(baseline_file)
        agent_results = load_results(agent_file)

        # Calculate metrics
        baseline_metrics = calculate_metrics(baseline_results, expected_classes)
        agent_metrics = calculate_metrics(agent_results, expected_classes)

        all_metrics[dataset_name] = {
            "baseline": baseline_metrics,
            "agent": agent_metrics,
            "expected_classes": expected_classes
        }

        # Print comparison
        if baseline_results or agent_results:
            print_dataset_comparison(dataset_name, baseline_metrics, agent_metrics, expected_classes)
        else:
            print(f"\n{dataset_name}: No results found")

    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)
    print(f"\n{'Dataset':<35} {'Baseline':<12} {'Agent':<12} {'Diff':<10}")
    print("-" * 70)

    for dataset_name, data in all_metrics.items():
        b_acc = data["baseline"]["accuracy"]
        a_acc = data["agent"]["accuracy"]
        diff = a_acc - b_acc
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"
        print(f"{dataset_name:<35} {b_acc:.1f}%{'':<7} {a_acc:.1f}%{'':<7} {diff_str}")

    # Generate and save report
    if all_metrics:
        report = generate_report(all_metrics)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        report_file = RESULTS_DIR / "evaluation_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    evaluate()
