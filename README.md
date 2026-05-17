# fMRI-analysis
Visualization of MRI image, with according pressure, temperature, -3dB at the ROI resulted from k-plan simulation software.

# Focused Ultrasound (FUS) Post-Processing & Reporting 

This script provides automated post-processing and reporting for Focused Ultrasound (FUS) simulation data targeting the **sgACC (Subgenual Anterior Cingulate Cortex - BA25)** for participant `sub-04`.

---

## Required Project Outputs

The script analyzes the pressure and temperature fields simulated by kPlan, calculates focal zone targeting metrics, and generates the following mandatory outputs:

1.  **ROI Figures:** A 3-plane view (Axial, Coronal, Sagittal) showing the focal zones overlaid on your specific targets (`sgACC_L` and `sgACC_R`).
2.  **Pressure Map:** Color-coded cross-sections cutting directly through the global peak pressure voxel, complete with structured tissue boundary outlines.
3.  **Temperature Map:** High-resolution visualization extracting peak temperature distributions across different anatomical structures.
4.  **-3dB & -6dB Focus Overlap Metrics:** Exact volumes ($mm^3$) and percentages (%) showing how much of the ultrasound focus successfully overlaps with the `sgACC` masks. (-3dB: high-intensity core, -6dB: full focal zone surrounding ROI).

---

## Input

| :--- | :--- |
| `TN-SV-CITRUS-offline-sub-04-Segmentation.nii.gz` | SimNIBS tissue segmentation mask (Brain, Skull, Scalp, Eyes). |
| `TN-SV-CITRUS-offline-sub-04-sgACC_BA25_L_kplan.nii.gz` | Left sgACC mask. |
| `TN-SV-CITRUS-offline-sub-04-sgACC_BA25_R_kplan.nii.gz` | Right sgACC mask. |
| `TN-SV-CITRUS-offline-sub-04-sub-04_T1w_kplan.nii` | Structural T1w image. |
|  T1w image: https://drive.google.com/file/d/1rUmDju0mYRLf0ZbqaW597_P_KF5_7ftq/view?usp=sharing  |

> 💡 **Note:** `TARGET_MASK_FOLDER` only needs to contain your two specific Left and Right `sgACC` NIfTI files. Broader cortical and subcortical brain regions are automatically fetched from the standardized **Harvard-Oxford Atlas** using the `nilearn` library.

---

## Script Configuration

Before running the pipeline, open your Python script and update the absolute folder paths to match the directory setup:

```python

SIMNIBS_PATH        = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-Segmentation.nii.gz"
T1_PATH             = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-sub-04_T1w_kplan.nii"
TARGET_MASK_FOLDER  = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/mask folder" # Folder with two sgACC masks
OUTPUT_DIR          = "/Users/hoaithunguyen/Projects/fMRI analysis/results"
