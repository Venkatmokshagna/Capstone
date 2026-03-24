import os
from PIL import Image, ImageStat

folder = r"c:\Users\moksh\Downloads\waterbornedisease-main\waterbornedisease-main\static\uploads\ai_samples"

for file in os.listdir(folder):
    if not file.endswith(".jpg"): continue
    
    path = os.path.join(folder, file)
    size = os.path.getsize(path)
    if size < 200000: continue # Skip small ones
    
    try:
        image = Image.open(path).convert("RGB")
        stat = ImageStat.Stat(image)
        avg_r, avg_g, avg_b = stat.mean
        std_r, std_g, std_b = stat.stddev
        
        avg_std = (std_r + std_g + std_b) / 3.0
        total_color = avg_r + avg_g + avg_b + 1.0
        
        dirtiness_score = 0.0
        details = []
        
        if avg_std > 40:
            penalty = (avg_std - 40) / 100.0
            dirtiness_score += penalty
            details.append(f"Texture={penalty:.2f}")
            
        if avg_r > avg_b * 1.05:
            dirtiness_score += 0.35
            details.append("R>B")
        if avg_g > avg_b * 1.05:
            dirtiness_score += 0.25
            details.append("G>B")
            
        if total_color < 250:
            dirtiness_score += 0.3
            details.append("Dark")
            
        pred_base = 1.0 - dirtiness_score
        pred_jitter = pred_base + (len(file) % 10) / 200.0
        pred_final = max(0.05, min(0.95, pred_jitter))
        
        print(f"File: {file} | Size: {size/1024:.0f}KB | RGB: {avg_r:.0f},{avg_g:.0f},{avg_b:.0f} | Std: {avg_std:.0f} | Dirt={dirtiness_score:.2f} {details} | Pred={pred_final:.2f}")
    except Exception as e:
        print(f"Error {file}: {e}")
