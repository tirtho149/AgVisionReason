#!/bin/bash
# Standalone CoT-based disease classification command
# Usage: bash run_cot_single.sh [image_path]
# Example: bash run_cot_single.sh /Users/muhammadarbabarshad/build2026-local/reasoning/test_data/Foliar_Disease_Stress/images/test_001.jpg

IMAGE_PATH="${1:-/Users/muhammadarbabarshad/build2026-local/reasoning/test_data/Foliar_Disease_Stress/images/test_001.jpg}"
PROJECT_DIR="/Users/muhammadarbabarshad/build2026-local/reasoning"

claude -p "You are a plant disease classification agent that follows a structured Chain-of-Thought (CoT) diagnostic framework.

DATASET: Mango Leaf Diseases
AVAILABLE CLASSES: ['Anthracnose', 'Bacterial_Canker', 'Cutting_Weevil', 'Die_Back', 'Gall_Midge', 'Powdery_Mildew', 'Sooty_Mould']

TASK: Classify the disease/condition in the image at: ${IMAGE_PATH}

INSTRUCTIONS:
1. Read the knowledge base at ${PROJECT_DIR}/disease_symptoms.md
2. View the target image at ${IMAGE_PATH}
3. Follow the DIAGNOSTIC COT FRAMEWORK below step by step — write out your reasoning for each step before moving to the next
4. You MUST view reference images for your top 2-3 candidate classes using the EXACT paths listed in the knowledge base (they are relative to ${PROJECT_DIR})
5. After completing all steps, make your prediction

---
DIAGNOSTIC COT FRAMEWORK (follow each step in order):

STEP 1 — CONTEXT:
Identify the host crop (mango), note any visible context clues (field vs lab setting, lighting, background).

STEP 2 — LOCALIZE: WHERE/WHAT IS AFFECTED:
Which plant part is shown (leaf, stem, fruit, seedling)? Is it a single leaf or multiple? Is there a visible organism present?

STEP 3 — SYMPTOM/TRAIT DESCRIPTION (discriminating traits):
Describe precisely what you see — color, pattern, texture, location on the organ, morphology. Be specific:
- Is the damage FLAT (spots/lesions/coating) or RAISED (bumps/galls/blisters)?
- Is it SUPERFICIAL (sitting on surface, can be scraped off) or EMBEDDED (penetrating tissue)?
- Are there DISCRETE spots or a CONTINUOUS coating/film?
- What is the SHAPE of damage (angular, circular, irregular, semicircular notches)?
- Is there a HALO (yellow/red border) around lesions?
- Are there HOLES where tissue has fallen out?

STEP 4 — STAGE AND PROGRESSION:
What growth stage is the leaf (young/tender vs mature)? Is the damage progressing tip-to-base, margin-inward, or scattered? Are there signs of different stages of the same damage (old + new lesions)?

STEP 5 — PATTERN IN SPACE:
Is the damage uniform across the leaf or concentrated in patches? Is it along veins, at margins, at the tip, or randomly scattered? One side vs both sides of the midrib?

STEP 6 — CONFIRMATORY CHECKS (compare with references):
Based on steps 1-5, identify your top 2-3 candidate classes. View reference images for each candidate from the knowledge base. Compare the specific discriminating traits you noted in Step 3 against what you see in the references. Pay special attention to:
- FLAT spots vs RAISED bumps (distinguishes Anthracnose/Bacterial_Canker/Sooty_Mould from Gall_Midge)
- SUPERFICIAL coating vs EMBEDDED lesions (distinguishes Sooty_Mould from Anthracnose/Bacterial_Canker)
- MECHANICAL damage (cuts/tears) vs BIOLOGICAL damage (spots/lesions) (distinguishes Cutting_Weevil from all others)
- PROGRESSIVE tip-to-base browning vs SCATTERED spots (distinguishes Die_Back from spot diseases)
---

OUTPUT: After completing all 6 steps, return a JSON object:
{\"prediction\": \"class_name\"}

The prediction must be exactly one of: ['Anthracnose', 'Bacterial_Canker', 'Cutting_Weevil', 'Die_Back', 'Gall_Midge', 'Powdery_Mildew', 'Sooty_Mould']" \
  --allowedTools "Read" \
  --model haiku \
  --output-format stream-json \
  --verbose 2>/dev/null | python3 -c "
import sys, json, re
trace = []
result = {}
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    obj = json.loads(line)
    if obj.get('type') == 'assistant':
        for c in obj.get('message',{}).get('content',[]):
            if c.get('type') == 'tool_use':
                fp = c.get('input',{}).get('file_path','')
                short = fp.split('reasoning/')[-1] if 'reasoning/' in fp else fp
                trace.append(f'  READ: {short}')
            elif c.get('type') == 'text' and c.get('text','').strip():
                trace.append(f'  TEXT: {c[\"text\"].strip()}')
    elif obj.get('type') == 'result':
        result = obj

print('=== TRACE ===')
for t in trace:
    print(t)
    print()
print('=== RESULT ===')
print(f'Turns: {result.get(\"num_turns\")}')
print(f'Duration: {result.get(\"duration_ms\",0)/1000:.1f}s')
print(f'Cost: \${result.get(\"total_cost_usd\",0):.4f}')
m = re.search(r'\"prediction\":\s*\"([^\"]+)\"', result.get('result',''))
print(f'Prediction: {m.group(1) if m else \"UNKNOWN\"}')
"
