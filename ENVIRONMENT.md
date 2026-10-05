# Locked software environment

Operating system: Windows-10-10.0.19045-SP0

Two environments are used. The econometric models (GARCH, GJR-GARCH, GARCH-X, HAR and its variants, all tests)
run in the first; the neural networks and SHAP run in the second, which carries a CUDA-enabled PyTorch build.

## Environment A — econometrics and evaluation

| Component | Version |
|---|---|
| Python | 3.13.9 |
| numpy | 2.1.3 |
| pandas | 2.2.3 |
| scipy | 1.15.3 |
| statsmodels | 0.14.4 |
| arch | 8.0.0 |
| scikit-learn | 1.6.1 |
| matplotlib | 3.10.0 |

## Environment B — deep learning (GPU)

| Component | Version |
|---|---|
| Python | 3.11.15 |
| PyTorch | 2.13.0+cu126 |
| CUDA (torch build) | 12.6 |
| cuDNN | 91002 |
| GPU | NVIDIA GeForce GTX 1060 3GB |
| Compute capability | 6.1 |
| numpy | 2.4.6 |
| pandas | 3.0.5 |
| shap | 0.51.0 |

## Notes

- All deep learning results reported in the paper come from Environment B. Section 7.2 documents that an earlier
  build (PyTorch 2.6.0 with CUDA 12.4) shifts the measured QLIKE by about 0.011, the same order of magnitude as
  the architecture component of the decomposition. Results from the two builds must not be mixed.
- Training is deterministic within a fixed environment: repeating a run with the same seed reproduces the forecasts
  exactly (maximum absolute difference 0.0 across the 752 evaluation days).
- The GPU is a Pascal-generation card (compute capability 6.1). PyTorch wheels built against CUDA 12.8 or later no
  longer ship kernels for this architecture, so a cu126 build is required.
- Environment A keeps numpy and torch apart deliberately: its numpy is an MKL build whose OpenMP runtime clashes
  with the one bundled with torch.

## Recreate Environment B

```
conda create -n ladder python=3.11
conda activate ladder
pip install --index-url https://download.pytorch.org/whl/cu126 "torch==2.13.0+cu126"
pip install numpy pandas scipy shap pyarrow
```
