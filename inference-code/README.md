# Inference Code

This directory contains code and resources related to model inference, predominantly used for bulk-generating images from prompts and evaluating them.

## `run_generate.py`

This script automates the process of generating imagery via multiple `diffusers` pipelines and computes quantitative evaluation metrics.

*   **Supported Models**: Evaluates standard and turbo models including Sana, Z-Image-Turbo, and SD 3.5 Large Turbo using a unified pipeline.
*   **Evaluation Metrics**: Analyzes generated outputs by integrating `PickScore` and `CLIP score` to objectively score image-text alignment for every generated image.
*   **Workflow**: Reads prompt datasets sequentially from `./txt_files_2`, generates the images locally, and automatically logs per-folder summary scores along with individualized prompt metrics.

We can also set the manual seed for reproducibility.

### Example Usage

```bash
# Run with the default model (Sana)
python run_generate.py

# Run with a specific model
python run_generate.py --model z-image-turbo
python run_generate.py --model sd3.5
python run_generate.py --model sana
```
