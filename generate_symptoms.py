#!/usr/bin/env python3
"""
Generate disease symptoms using GPT API.
Creates disease_symptoms.md with 4-5 line descriptions and reference image paths.
"""

import os
from pathlib import Path
from dotenv import dotenv_values
from openai import OpenAI

# Load environment variables from .env file (override existing)
env_file = Path(__file__).parent / ".env"
env_vars = dotenv_values(env_file)

# Set environment variables (override any malformed ones)
for key, value in env_vars.items():
    if value:  # Only set if value exists
        os.environ[key] = value

# Configuration
DATASET_DIR = Path(__file__).parent / "Plant_Disease_Dataset"
OUTPUT_FILE = Path(__file__).parent / "disease_symptoms.md"

# Disease categories and their descriptions for context
CATEGORIES = {
    "Foliar_Disease_Stress": {
        "description": "Mango Leaf Diseases",
        "context": "mango tree leaves"
    },
    "Disease_Severity": {
        "description": "Yellow Rust Severity in Wheat",
        "context": "wheat plants affected by yellow rust disease"
    }
}


def get_diseases_from_dataset():
    """Scan dataset directory to get all disease classes."""
    diseases = {}

    for category in CATEGORIES:
        category_path = DATASET_DIR / category
        if category_path.exists():
            disease_folders = [d.name for d in category_path.iterdir() if d.is_dir()]
            diseases[category] = sorted(disease_folders)

    return diseases


def get_reference_images(category: str, disease: str, count: int = 3):
    """Get paths to reference images for a disease."""
    disease_path = DATASET_DIR / category / disease
    images = []

    if disease_path.exists():
        image_files = sorted([f.name for f in disease_path.iterdir()
                             if f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
        images = image_files[:count]

    return images


def generate_symptom_description(client: OpenAI, disease_name: str, category: str) -> str:
    """Call GPT API to generate symptom description."""

    # Clean up disease name for prompt
    clean_name = disease_name.replace("_", " ")
    context = CATEGORIES[category]["context"]

    # Different prompts based on category type
    if category == "Disease_Severity":
        prompt = f"""Write a 4-5 line description of the visual characteristics for "{clean_name}" severity level in yellow rust disease on wheat plants.

Focus on:
- Amount and density of rust pustules visible
- Color intensity of the rust (yellow/orange)
- Coverage percentage on leaf surface
- Overall leaf health indicators
- How this severity level differs from others

Be specific about visual features a machine learning model would use to identify this severity level. Write in plain text, not bullet points."""
    else:
        prompt = f"""Write a 4-5 line description of the visual symptoms for "{clean_name}" disease on {context}.

Focus on:
- Distinctive visual patterns (spots, lesions, discoloration)
- Color characteristics
- Shape and distribution of symptoms
- Texture changes
- Unique identifiers that distinguish this from other diseases

Be specific about visual features a machine learning model would use to identify this disease. Write in plain text, not bullet points."""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=300,
        messages=[
            {"role": "system", "content": "You are a plant pathology expert. Provide concise, accurate visual symptom descriptions."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


def generate_knowledge_base():
    """Generate the complete knowledge base markdown file."""

    client = OpenAI()  # Uses OPENAI_API_KEY env var
    diseases = get_diseases_from_dataset()

    print("=" * 60)
    print("GENERATING DISEASE SYMPTOMS KNOWLEDGE BASE")
    print("=" * 60)

    markdown_content = """# Plant Disease Knowledge Base

This knowledge base contains visual symptom descriptions for plant disease classification.
Generated using GPT-4 for use with Claude Haiku classification.

---

"""

    for category, disease_list in diseases.items():
        category_info = CATEGORIES[category]

        markdown_content += f"## {category_info['description']}\n\n"
        print(f"\n[{category_info['description']}]")

        for disease in disease_list:
            print(f"  Generating symptoms for: {disease}...", end=" ", flush=True)

            # Generate symptom description
            symptoms = generate_symptom_description(client, disease, category)

            # Get reference images
            ref_images = get_reference_images(category, disease)

            # Format disease name for display
            display_name = disease.replace("_", " ")

            markdown_content += f"### {display_name}\n\n"
            markdown_content += f"**Symptoms:**\n{symptoms}\n\n"
            markdown_content += "**Reference Images:**\n"

            for img in ref_images:
                rel_path = f"Plant_Disease_Dataset/{category}/{disease}/{img}"
                markdown_content += f"- {rel_path}\n"

            markdown_content += "\n---\n\n"

            print("Done")

    # Write to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(markdown_content)

    print("\n" + "=" * 60)
    print(f"Knowledge base saved to: {OUTPUT_FILE}")
    print("=" * 60)

    return OUTPUT_FILE


if __name__ == "__main__":
    generate_knowledge_base()
