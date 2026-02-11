#!/usr/bin/env python3
"""
Prepare anonymized test data to prevent label leakage.
Creates separate test sets for each dataset type (Foliar_Disease_Stress, Disease_Severity).
"""

import os
import json
import shutil
import random
import argparse
from pathlib import Path

# Configuration
SOURCE_DIR = Path(__file__).parent / "Plant_Disease_Dataset"
OUTPUT_DIR = Path(__file__).parent / "test_data"

# Dataset categories
DATASETS = {
    "Foliar_Disease_Stress": {
        "description": "Mango Leaf Diseases",
        "classes": ["Anthracnose", "Bacterial_Canker", "Cutting_Weevil", "Die_Back",
                    "Gall_Midge", "Powdery_Mildew", "Sooty_Mould"]
    },
    "Disease_Severity": {
        "description": "Yellow Rust Severity Levels",
        "classes": ["Resistant_R", "Moderately_Resistant_MR", "MRMS",
                    "Moderately_Susceptible_MS", "Susceptible_S"]
    }
}


def get_images_for_dataset(source_dir: Path, dataset_name: str) -> list:
    """Get all images for a specific dataset."""
    images = []
    dataset_dir = source_dir / dataset_name

    if not dataset_dir.exists():
        return images

    for disease_dir in dataset_dir.iterdir():
        if disease_dir.is_dir():
            label = disease_dir.name
            for img_file in disease_dir.iterdir():
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    images.append({
                        "source_path": str(img_file),
                        "label": label
                    })

    return images


def prepare_dataset(dataset_name: str, per_class: int, seed: int):
    """Prepare anonymized test data for a single dataset."""

    print(f"\n{'='*60}")
    print(f"PREPARING: {dataset_name}")
    print(f"Description: {DATASETS[dataset_name]['description']}")
    print(f"{'='*60}")

    random.seed(seed)

    # Get all images for this dataset
    all_images = get_images_for_dataset(SOURCE_DIR, dataset_name)
    print(f"Total images in source: {len(all_images)}")

    # Group by label
    by_label = {}
    for img in all_images:
        label = img["label"]
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(img)

    expected_classes = DATASETS[dataset_name]["classes"]
    print(f"Expected classes: {len(expected_classes)}")
    for label in expected_classes:
        count = len(by_label.get(label, []))
        print(f"  {label}: {count} images")

    # Sample per_class images from each class
    selected = []
    for label in expected_classes:
        imgs = by_label.get(label, [])
        sample_count = min(per_class, len(imgs))
        if sample_count > 0:
            sampled = random.sample(imgs, sample_count)
            selected.extend(sampled)

    print(f"\nSelected {len(selected)} images ({per_class} per class)")

    # Shuffle and assign random IDs
    random.shuffle(selected)

    # Create output directory for this dataset
    dataset_output_dir = OUTPUT_DIR / dataset_name
    images_dir = dataset_output_dir / "images"

    if dataset_output_dir.exists():
        shutil.rmtree(dataset_output_dir)
    images_dir.mkdir(parents=True)

    # Copy images with anonymous names and build ground truth
    ground_truth = {}

    print("\nCopying images...")
    for i, img in enumerate(selected):
        # Create anonymous filename
        ext = Path(img["source_path"]).suffix
        anon_name = f"test_{i+1:03d}{ext}"

        # Copy file
        dest_path = images_dir / anon_name
        shutil.copy2(img["source_path"], dest_path)

        # Store ground truth
        ground_truth[anon_name] = {
            "label": img["label"],
            "original_path": img["source_path"]
        }

        print(f"  {anon_name} <- {img['label']}")

    # Save ground truth
    ground_truth_file = dataset_output_dir / "ground_truth.json"
    with open(ground_truth_file, 'w') as f:
        json.dump({
            "dataset_name": dataset_name,
            "description": DATASETS[dataset_name]["description"],
            "expected_classes": expected_classes,
            "images": ground_truth
        }, f, indent=2)

    print(f"\nSaved: {ground_truth_file}")
    print(f"Total images: {len(selected)}")

    return len(selected)


def prepare_all_test_data(per_class: int = 2, seed: int = 42):
    """Create anonymized test datasets for all dataset types."""

    print("=" * 60)
    print("PREPARING ANONYMIZED TEST DATA (Per Dataset)")
    print("=" * 60)

    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    total_images = 0
    summary = {}

    for dataset_name in DATASETS:
        count = prepare_dataset(dataset_name, per_class, seed)
        summary[dataset_name] = count
        total_images += count

    # Save overall metadata
    metadata = {
        "total_images": total_images,
        "images_per_class": per_class,
        "seed": seed,
        "datasets": {
            name: {
                "description": DATASETS[name]["description"],
                "num_classes": len(DATASETS[name]["classes"]),
                "num_images": summary[name],
                "classes": DATASETS[name]["classes"]
            }
            for name in DATASETS
        }
    }

    metadata_file = OUTPUT_DIR / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 60)
    print("TEST DATA PREPARED")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"\nDatasets:")
    for name, count in summary.items():
        print(f"  {name}: {count} images ({len(DATASETS[name]['classes'])} classes)")
    print(f"\nTotal: {total_images} images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare anonymized test data")
    parser.add_argument("--per-class", type=int, default=2,
                        help="Number of images per class (default: 2)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    prepare_all_test_data(per_class=args.per_class, seed=args.seed)
