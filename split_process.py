from PIL import Image
import os
from pathlib import Path

# ---- USER SETTINGS ----
input_folder = "/Users/arpan/Documents/Github/Python/BookIllustrations/pip_the_thankful_pumpkin"  # Change to your folder path
dpi = 300                           # Print quality
width_inch = 12.25
height_inch = 9.25

# Convert target inches to pixels
target_width = int(width_inch * dpi)
target_height = int(height_inch * dpi)

# ---- STEP 1: Create output folder ----
output_folder = os.path.join(input_folder, "processed_images")
os.makedirs(output_folder, exist_ok=True)

# ---- STEP 2: Process book_cover.png ----
book_cover_path = os.path.join(input_folder, "book_cover.png")
if os.path.exists(book_cover_path):
    print(f"Processing book_cover.png...")
    img = Image.open(book_cover_path)
    img_resized = img.resize((target_width, target_height), Image.LANCZOS)
    output_path = os.path.join(output_folder, "book_cover.png")
    img_resized.save(output_path, dpi=(dpi, dpi))
    print(f"✅ Saved: book_cover.png")
else:
    print("⚠️  book_cover.png not found")

# ---- STEP 3: Process img_<number>.png files ----
img_files = sorted([f for f in os.listdir(input_folder) if f.startswith("img_") and f.endswith(".png")])

for img_file in img_files:
    # Extract number from filename (e.g., img_1.png -> 1)
    img_number = img_file.replace("img_", "").replace(".png", "")
    
    print(f"Processing {img_file}...")
    
    # Load and resize image
    img_path = os.path.join(input_folder, img_file)
    img = Image.open(img_path)
    img_resized = img.resize((target_width, target_height), Image.LANCZOS)
    
    # Split into halves
    midpoint = target_width // 2
    left_half = img_resized.crop((0, 0, midpoint, target_height))
    right_half = img_resized.crop((midpoint, 0, target_width, target_height))
    
    # Save left and right halves
    left_path = os.path.join(output_folder, f"img_left_{img_number}.png")
    right_path = os.path.join(output_folder, f"img_right_{img_number}.png")
    
    left_half.save(left_path, dpi=(dpi, dpi))
    right_half.save(right_path, dpi=(dpi, dpi))
    
    print(f"✅ Saved: img_left_{img_number}.png and img_right_{img_number}.png")

print("\n🎉 All done! Processed images saved in:", output_folder)
print(f"\nResults:")
print(f"• book_cover.png: {width_inch}\" × {height_inch}\"")
print(f"• {len(img_files)} images split into left/right halves (each {width_inch/2}\" × {height_inch}\")")
