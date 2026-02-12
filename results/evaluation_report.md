# Evaluation Report

Generated: 2026-02-11 21:20:50

## Overall Summary

| Dataset | Baseline | Agent | Improvement |
|---------|----------|-------|-------------|
| Disease_Severity | 40.0% | 20.0% | -20.0% |
| Foliar_Disease_Stress | 42.9% | 64.3% | +21.4% |

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
- **Agent**: 9/14 (64.3%)

### Per-Class Results

| Class | Baseline | Agent | Diff |
|-------|----------|-------|------|
| Anthracnose | 2/2 | 2/2 | 0% |
| Bacterial_Canker | 0/2 | 1/2 | +50% |
| Cutting_Weevil | 1/2 | 2/2 | +50% |
| Die_Back | 1/2 | 1/2 | 0% |
| Gall_Midge | 0/2 | 1/2 | +50% |
| Powdery_Mildew | 0/2 | 0/2 | 0% |
| Sooty_Mould | 2/2 | 2/2 | 0% |
