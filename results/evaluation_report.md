# Evaluation Report

Generated: 2026-02-11 20:32:34

## Overall Summary

| Dataset | Baseline | Agent | Improvement |
|---------|----------|-------|-------------|
| Disease_Severity | 40.0% | 20.0% | -20.0% |
| Foliar_Disease_Stress | 42.9% | 42.9% | 0.0% |

---

## Disease_Severity

### Summary
- **Baseline**: 4/10 (40.0%)
- **Agent**: 2/10 (20.0%)

### Per-Class Results

| Class | Baseline | Agent | Diff |
|-------|----------|-------|------|
| Resistant_R | 1/2 | 1/2 | 0% |
| Moderately_Resistant_MR | 0/2 | 0/2 | 0% |
| MRMS | 0/2 | 0/2 | 0% |
| Moderately_Susceptible_MS | 2/2 | 1/2 | -50% |
| Susceptible_S | 1/2 | 0/2 | -50% |

---

## Foliar_Disease_Stress

### Summary
- **Baseline**: 6/14 (42.9%)
- **Agent**: 6/14 (42.9%)

### Per-Class Results

| Class | Baseline | Agent | Diff |
|-------|----------|-------|------|
| Anthracnose | 2/2 | 0/2 | -100% |
| Bacterial_Canker | 0/2 | 1/2 | +50% |
| Cutting_Weevil | 1/2 | 1/2 | 0% |
| Die_Back | 1/2 | 2/2 | +50% |
| Gall_Midge | 0/2 | 1/2 | +50% |
| Powdery_Mildew | 0/2 | 1/2 | +50% |
| Sooty_Mould | 2/2 | 0/2 | -100% |
