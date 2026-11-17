"""Hoja de storyboard: stills numerados con su texto. Uso: storyboard.py comp carpeta 't1|texto' 't2|texto' ..."""
import sys, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
comp, d, items = sys.argv[1], sys.argv[2], sys.argv[3:]
W, H = 360, 640; cols = 3; rows = (len(items) + cols - 1) // cols; TH = 150
sheet = Image.new("RGB", (cols * (W + 20) + 20, rows * (H + TH + 20) + 20), "#0f0c20")
dr = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("DejaVuSans.ttf", 20)
except OSError: font = ImageFont.load_default()
for i, it in enumerate(items):
    t, txt = it.split("|", 1); f = round(float(t) * 30)
    out = f"{d}/s{i+1}.png"
    subprocess.run(["npx", "remotion", "still", "src/index.ts", comp, out, f"--frame={f}", "--log=error"], check=True)
    im = Image.open(out).convert("RGB").resize((W, H))
    x = 20 + (i % cols) * (W + 20); y = 20 + (i // cols) * (H + TH + 20)
    sheet.paste(im, (x, y))
    dr.text((x, y + H + 8), f"{i+1}  ({t} s)", fill="#ff8fbd", font=font)
    for j, line in enumerate(textwrap.wrap(txt, 34)[:4]): dr.text((x, y + H + 36 + j * 26), line, fill="#f4ecff", font=font)
sheet.save(f"{d}/storyboard.png"); print(f"{d}/storyboard.png")
