# Data Curation Code

This directory contains code and scripts for data curation, primarily focused on creating controlled datasets of perturbed text prompts.

## `generate_all_datasets.py`

This script takes an initial input file of text-to-image prompts (`diffusiondb_prompts.txt`) and generates 10 distinct variations. By randomly selecting a subset of eligible prompts, it injects multiple types and intensities of errors:

*   **Error Types**: Typos, Language Discrepancies (swapping words for French/Spanish equivalents), and Grammar distortions.
*   **Intensities**: Low (1 error), Medium (3 errors), and High (5 errors).
*   **Output**: Produces a `control.txt` file and 9 targeted text files documenting each error level across each type, allowing for systematic robustness evaluation of image generation models.

### Example Usage

```bash
# Generate datasets with default settings (200 samples, seed 42)
python generate_all_datasets.py

# Generate datasets with custom settings
python generate_all_datasets.py --n-samples 500 --seed 123
```
