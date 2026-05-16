# fMRI-analysis
Visualization of MRI image, with according pressure, temperature, -3dB at the ROI resulted from k-plan simulation software.

# Focused Ultrasound (FUS) Post-Processing & Reporting 

This script provides automated post-processing and reporting for Focused Ultrasound (FUS) simulation data targeting the **sgACC (Subgenual Anterior Cingulate Cortex - BA25)** for participant `sub-04`.

---

## Required Project Outputs

The script analyzes the pressure and temperature fields simulated by kPlan, calculates focal zone targeting metrics, and generates the following mandatory outputs:

1.  **ROI Figures (Panel A):** A 3-plane view (Axial, Coronal, Sagittal) showing the focal zones overlaid on your specific targets (`sgACC_L` and `sgACC_R`).
2.  **Pressure Map (Panel D):** Color-coded cross-sections cutting directly through the global peak pressure voxel, complete with structured tissue boundary outlines.
3.  **Temperature Map (Panel B/D):** High-resolution visualization extracting peak temperature distributions across different anatomical structures.
4.  **-3dB & -6dB Focus Overlap Metrics:** Exact volumes ($mm^3$) and percentages (%) showing how much of the ultrasound focus successfully overlaps with the `sgACC` masks.

---

## 📁 Input Files Checklist

Ensure the following files from your local drive are properly mapped in the configuration section of the script:

| Your Exact Filename | Description / Role in Pipeline |
| :--- | :--- |
| `sub-04_..._defocused.h5` | kPlan Results file containing raw simulated pressure and temperature fields. |
| `TN-SV-CITRUS-offline-sub-04-Segmentation.nii.gz` | SimNIBS tissue segmentation mask (Brain, Skull, Scalp, Eyes). |
| `TN-SV-CITRUS-offline-sub-04-sgACC_BA25_L_kplan.nii.gz` | Left sgACC target mask. |
| `TN-SV-CITRUS-offline-sub-04-sgACC_BA25_R_kplan.nii.gz` | Right sgACC target mask. |
| `TN-SV-CITRUS-offline-sub-04-sub-04_T1w_kplan.nii` | Structural T1w image used as the anatomical background for plots. |
|  T1w image: https://drive.google.com/file/d/1rUmDju0mYRLf0ZbqaW597_P_KF5_7ftq/view?usp=sharing  |

> 💡 **Note:** Your `TARGET_MASK_FOLDER` only needs to contain your two specific `sgACC` NIfTI files. Broader cortical and subcortical brain regions are automatically fetched from the standardized **Harvard-Oxford Atlas** using the `nilearn` library.

---

## Script Configuration

Before running the pipeline, open your Python script and update the absolute folder paths to match your Mac directory setup:

```python
H5_FILES = [
    "/Users/hoaithunguyen/Documents/Masters/thesis/defocused element file/sub-04_L_pos-5_I-6_defocused.h5",
]

SIMNIBS_PATH        = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-Segmentation.nii.gz"
T1_PATH             = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-sub-04_T1w_kplan.nii"
TARGET_MASK_FOLDER  = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/mask folder" # Folder with your sgACC masks
OUTPUT_DIR          = "/Users/hoaithunguyen/Projects/fMRI analysis/results"
