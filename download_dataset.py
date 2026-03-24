import os
import zipfile
import shutil
import glob

# Ensure Kaggle API is authenticated (requires ~/.kaggle/kaggle.json)
try:
    import kaggle
except OSError as e:
    print("❌ Kaggle Authentication Error:", e)
    print("Please make sure you have placed your kaggle.json file in the correct directory.")
    print("On Windows: C:\\Users\\moksh\\.kaggle\\kaggle.json")
    exit(1)

# The dataset slug on Kaggle
DATASET = "mssmartypants/water-quality"
TARGET_DIR = "dataset"

print(f"📥 Downloading dataset {DATASET} from Kaggle...")
kaggle.api.dataset_download_files(DATASET, path='.', unzip=False)

zip_file = [f for f in glob.glob("*.zip") if "water-quality" in f.lower()]
if not zip_file:
    print("❌ Downloaded zip file not found!")
    exit(1)

zip_file = zip_file[0]
print(f"📦 Extracting {zip_file}...")

extract_dir = "temp_dataset"
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print("📁 Organizing images into dataset/clean and dataset/contaminated...")

os.makedirs(os.path.join(TARGET_DIR, "clean"), exist_ok=True)
os.makedirs(os.path.join(TARGET_DIR, "contaminated"), exist_ok=True)

# Recursively find all images and move them based on folder names
moved = 0
for root, dirs, files in os.walk(extract_dir):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            src = os.path.join(root, file)
            # Determine category based on folder path
            lower_path = src.lower()
            if "clean" in lower_path or "safe" in lower_path:
                shutil.move(src, os.path.join(TARGET_DIR, "clean", file))
                moved += 1
            elif "dirty" in lower_path or "contaminat" in lower_path or "pollut" in lower_path:
                shutil.move(src, os.path.join(TARGET_DIR, "contaminated", file))
                moved += 1

print(f"✅ Successfully moved {moved} images into the dataset folders.")

# Cleanup
os.remove(zip_file)
shutil.rmtree(extract_dir)

print("🚀 Ready! You can now run: python train_model.py")
