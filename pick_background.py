import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

ROOT = Path(__file__).resolve().parent
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)

window = tk.Tk()
window.withdraw()
window.attributes("-topmost", True)
chosen = filedialog.askopenfilename(
    title="Choose the background picture",
    filetypes=[("Pictures", "*.jpeg *.jpg *.png *.webp"), ("All files", "*.*")],
)
window.destroy()

if not chosen:
    print("No file chosen.")
else:
    src = Path(chosen)
    ext = src.suffix.lower()
    if ext not in (".jpeg", ".jpg", ".png", ".webp"):
        print(f"{ext or 'This file'} is not supported. Choose a JPEG, PNG or WEBP picture.")
    else:
        for old in assets.glob("background.*"):
            old.unlink()                      # remove an older background picture, if any
        dest = assets / f"background{ext}"
        shutil.copy(src, dest)
        size_kb = dest.stat().st_size // 1024
        print(f"Copied {src.name} -> {dest} ({size_kb} KB)")
        if size_kb > 2000:
            print("NOTE: this picture is large and may slow the pages down. Try a smaller version.")