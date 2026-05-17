import os
import glob
import h5py
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.image import resample_img
from nilearn import datasets as nilearn_datasets
import matplotlib
#matplotlib.use("Agg")                   # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import binary_dilation

# ════════════════════════════════════════════════════════════════════════════════
# INPUT / OUTPUT path
# ════════════════════════════════════════════════════════════════════════════════
H5_FILES = [
    "/Users/hoaithunguyen/Documents/Masters/thesis/defocused element file/sub-04_L_pos-5_I-6_defocused.h5"
]
T1_PATH = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-sub-04_T1w_kplan.nii"
SGACC_MASK_PATH = "/Users/hoaithunguyen/Projects/fMRI analysis/exp-focused/TN-SV-CITRUS-offline-sub-04-sgACC_BA25_L_kplan.nii"  # Đường dẫn tới riêng mask sgACC
OUTPUT_DIR = "/Users/hoaithunguyen/Projects/fMRI analysis/results"

RHO_C = 1.5e6  #


def build_affine(voxel_size_mm, origin_mm):
    affine = np.zeros((4, 4), dtype=np.float64)
    affine[0, 0], affine[1, 1], affine[2, 2] = voxel_size_mm, voxel_size_mm, voxel_size_mm
    affine[0:3, 3] = origin_mm
    affine[3, 3] = 1.0
    return affine


def match_shape(data, target_shape):
    out = np.zeros(target_shape, dtype=data.dtype)
    s = [min(a, b) for a, b in zip(data.shape, target_shape)]
    out[:s[0], :s[1], :s[2]] = data[:s[0], :s[1], :s[2]]
    return out


def load_pressure(h5_path, sonication_index):
    with h5py.File(h5_path, "r") as f:
        p_key = f"sonications/{sonication_index}/simulated_field/pressure_amplitude"
        dataset = f[p_key]
        scale_slope = float(dataset.attrs["scale_slope"].ravel()[0])
        scale_intercept = float(dataset.attrs["scale_intercept"].ravel()[0])

        pressure_pa = (dataset[:].astype(np.float32) * scale_slope + scale_intercept)
        pressure_pa = np.transpose(pressure_pa)

        mm_attrs = f["medium_properties/medium_mask"]
        grid_spacing_mm = float(mm_attrs.attrs["grid_spacing"].ravel()[0]) * 1000.0
        origin_mm = f["settings/grid/domain_position"][:].ravel()[:3] * 1000.0
        affine_sim = build_affine(grid_spacing_mm, origin_mm)

        frequency_hz = float(f[f"sonications/{sonication_index}/sonication_parameters/driving_frequency"][:].ravel()[0])
    return pressure_pa, affine_sim, pressure_pa.shape, frequency_hz


def load_thermal(h5_path, sonication_index):
    with h5py.File(h5_path, "r") as f:
        sf = f"sonications/{sonication_index}/simulated_field/temperature_maximum"
        scale_slope = float(f[sf].attrs["scale_slope"].ravel()[0])
        scale_intercept = float(f[sf].attrs["scale_intercept"].ravel()[0])
        temp_3d_degC = np.transpose(np.squeeze(f[sf][:].astype(np.float32) * scale_slope + scale_intercept))
    return temp_3d_degC


def get_best_slices(mask):
    coords = np.argwhere(mask > 0)
    return coords.mean(axis=0).astype(int) if coords.size > 0 else (0, 0, 0)


# ════════════════════════════════════════════════════════════════════════════════
# HÀM VẼ CÁC MAPS THEO YÊU CẦU
# ════════════════════════════════════════════════════════════════════════════════
def generate_outputs(h5_path, son_i):
    # 1. Load Data
    pressure_pa, affine_sim, grid_shape, freq_hz = load_pressure(h5_path, son_i)
    temp_3d_degC = load_thermal(h5_path, son_i)

    voxel_vol_mm3 = float(affine_sim[0, 0]) ** 3
    pressure_kpa = pressure_pa / 1000.0
    intensity_full = (pressure_pa ** 2) / (2 * RHO_C) / 1e4  # W/cm²

    # 2. Load và Resample sgACC Mask & T1 Background
    sgacc_img = nib.load(SGACC_MASK_PATH)
    sgacc_res = resample_img(sgacc_img, target_affine=affine_sim, target_shape=grid_shape,
                             interpolation="nearest").get_fdata()
    sgacc_mask = match_shape((np.squeeze(sgacc_res) > 0).astype(np.uint8), grid_shape)

    t1_img = nib.load(T1_PATH)
    t1_res = resample_img(t1_img, target_affine=affine_sim, target_shape=grid_shape, interpolation="linear").get_fdata()
    bg = match_shape(np.squeeze(t1_res).astype(np.float32), grid_shape)
    bg = (bg - bg.min()) / (bg.max() - bg.min())  # Chuẩn hóa nền T1

    # 3. Tính toán vùng -3dB Focus toàn cục và phần Overlap với sgACC
    peak_int_global = intensity_full.max()
    thr_3dB = 0.50 * peak_int_global
    mask_3dB = (intensity_full > thr_3dB).astype(np.uint8)
    overlap_mask = ((mask_3dB == 1) & (sgacc_mask == 1)).astype(np.uint8)

    # Lấy tọa độ lát cắt đi qua tâm vùng sgACC
    cx, cy, cz = get_best_slices(sgacc_mask)

    # 4. VẼ BIỂU ĐỒ (ROI Figures / Maps)
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), facecolor="#111111")

    # Colormaps cho Áp suất và Nhiệt độ
    cmap_pressure = LinearSegmentedColormap.from_list("p_map", ["#000000", "#0050ff", "#ff4500", "#ffffff"])
    cmap_thermal = plt.cm.hot

    planes = [
        ("Axial", bg[cx, :, :], pressure_kpa[cx, :, :], temp_3d_degC[cx, :, :], sgacc_mask[cx, :, :],
         mask_3dB[cx, :, :]),
        ("Coronal", bg[:, cy, :], pressure_kpa[:, cy, :], temp_3d_degC[:, cy, :], sgacc_mask[:, cy, :],
         mask_3dB[:, cy, :]),
        ("Sagittal", bg[:, :, cz], pressure_kpa[:, :, cz], temp_3d_degC[:, :, cz], sgacc_mask[:, :, cz],
         mask_3dB[:, :, cz]),
    ]

    for col_i, (title, bg_sl, p_sl, t_sl, sgacc_sl, f3_sl) in enumerate(planes):
        # --- HÀNG 1: PRESSURE MAP + -3dB Focus + sgACC Contour ---
        ax_p = axes[0, col_i]
        ax_p.imshow(bg_sl.T, cmap="gray", origin="lower", vmin=0, vmax=1)

        rgba_p = cmap_pressure(p_sl.T / (pressure_kpa.max() + 1e-12))
        rgba_p[..., 3] = (p_sl.T / (pressure_kpa.max() + 1e-12)) ** 0.5  # Alpha theo cường độ
        ax_p.imshow(rgba_p, origin="lower")

        # Vẽ viền vùng chồng lấp -3dB (màu vàng) và sgACC (màu xanh lục)
        if f3_sl.sum() > 0:
            ax_p.contour(f3_sl.T, levels=[0.5], colors=["#ffff00"], linewidths=1.2)
        if sgacc_sl.sum() > 0:
            ax_p.contour(sgacc_sl.T, levels=[0.5], colors=["#00ff00"], linewidths=1.5)

        ax_p.set_title(f"Pressure Map ({title})", color="white")
        ax_p.axis("off")

        # --- HÀNG 2: TEMPERATURE MAP + sgACC Contour ---
        ax_t = axes[1, col_i]
        ax_t.imshow(bg_sl.T, cmap="gray", origin="lower", vmin=0, vmax=1)

        rgba_t = cmap_thermal((t_sl.T - temp_3d_degC.min()) / (temp_3d_degC.max() - temp_3d_degC.min() + 1e-12))
        rgba_t[..., 3] = ((t_sl.T - temp_3d_degC.min()) / (temp_3d_degC.max() - temp_3d_degC.min() + 1e-12)) ** 0.5
        ax_t.imshow(rgba_t, origin="lower")

        if sgacc_sl.sum() > 0:
            ax_t.contour(sgacc_sl.T, levels=[0.5], colors=["#00ff00"], linewidths=1.5)

        ax_t.set_title(f"Temperature Map ({title})", color="white")
        ax_t.axis("off")

    # Lưu hình vẽ Maps
    fig.suptitle(f"Sonication {son_i} - Target: sgACC Overlap & Safety Maps", color="white", fontsize=16)
    fig.tight_layout()
    img_name = f"son{son_i}_sgACC_Analysis_Maps.png"
    fig.savefig(os.path.join(OUTPUT_DIR, img_name), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [Output] Đã lưu bản đồ trực quan: {img_name}")

    # 5. TÍNH TOÁN CÁC CHỈ SỐ ROI FIGURES (Lưu file CSV)
    sgacc_voxels = int(sgacc_mask.sum())
    overlap_voxels = int(overlap_mask.sum())

    p_in_sgacc = pressure_kpa[sgacc_mask == 1]
    t_in_sgacc = temp_3d_degC[sgacc_mask == 1]

    freq_mhz = freq_hz / 1e6
    mi_sgacc = (p_in_sgacc.max() / 1000.0) / np.sqrt(freq_mhz)  # Tính Mechanical Index

    roi_stats = {
        "Sonication": son_i,
        "Target_Name": "sgACC",
        "sgACC_Volume_mm3": round(sgacc_voxels * voxel_vol_mm3, 2),
        "Focus_Volume_3dB_mm3": round(mask_3dB.sum() * voxel_vol_mm3, 2),
        "Overlap_Volume_3dB_mm3": round(overlap_voxels * voxel_vol_mm3, 2),
        "Overlap_Percentage_of_sgACC": round((overlap_voxels / sgacc_voxels) * 100, 2) if sgacc_voxels > 0 else 0,
        "Peak_Pressure_sgACC_kPa": round(float(p_in_sgacc.max()), 2) if sgacc_voxels > 0 else 0,
        "Mean_Pressure_sgACC_kPa": round(float(p_in_sgacc.mean()), 2) if sgacc_voxels > 0 else 0,
        "Peak_Temperature_sgACC_degC": round(float(t_in_sgacc.max()), 2) if sgacc_voxels > 0 else 0,
        "Mean_Temperature_sgACC_degC": round(float(t_in_sgacc.mean()), 2) if sgacc_voxels > 0 else 0,
        "Mechanical_Index_sgACC": round(mi_sgacc, 2) if sgacc_voxels > 0 else 0
    }
    return roi_stats


# ════════════════════════════════════════════════════════════════════════════════
# TRÌNH ĐIỀU KHIỂN CHÍNH
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = []

    for h5_path in H5_FILES:
        if not os.path.exists(h5_path):
            print(f"Không tìm thấy file: {h5_path}")
            continue

        print(f"\nĐang xử lý: {os.path.basename(h5_path)}")
        with h5py.File(h5_path, "r") as f:
            n_sonications = len([k for k in f["sonications"].keys() if k.isdigit()])

        for son_i in range(1, n_sonications + 1):
            print(f"  --> Chạy Sonication {son_i}/{n_sonications}...")
            stats = generate_outputs(h5_path, son_i)
            all_results.append(stats)

    # Xuất file Excel/CSV kết quả dạng bảng (ROI Figures numerical data)
    if all_results:
        df = pd.DataFrame(all_results)
        csv_path = os.path.join(OUTPUT_DIR, "sgACC_Target_ROI_Figures.csv")
        df.to_csv(csv_path, index=False)
        print(f"\n[Thành công] Đã lưu bảng số liệu ROI Figures tại: {csv_path}")
        print(df.to_string(index=False))