"""Carousel slides (1080x1350) and story cards (1080x1920) in the brand style.
spec: {"brand":"jarvis"|"azure","kind":"carousel"|"story","hero":"optional/path.png","slides":[{"eyebrow":"","title":"","body":"","num":""}]}
usage: python3 cards.py spec.json out_prefix
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
REG = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
B = {
    "jarvis": dict(bg=(5, 8, 15), panel=(14, 22, 40), text=(231, 238, 249), muted=(147, 164, 191), accent=(255, 181, 71), glow=(76, 201, 255), tag="@jarvisworks.ai", name="JARVIS WORKS"),
    "azure": dict(bg=(11, 37, 69), panel=(20, 54, 96), text=(255, 255, 255), muted=(169, 200, 235), accent=(255, 200, 87), glow=(63, 169, 245), tag="@azure.cashoffers", name="AZURE CASH OFFERS"),
}

def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if cur and d.textlength(t, font=font) > maxw: out.append(cur); cur = w
            else: cur = t
        out.append(cur)
    return out

def bg(b, W, H):
    img = Image.new("RGB", (W, H), b["bg"]); d = ImageDraw.Draw(img)
    gc = tuple(int(c + (g - c) * 0.07) for c, g in zip(b["bg"], b["glow"]))
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=gc)
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=gc)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 520, -260, W + 200, 460], fill=b["glow"] + (60,))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    return Image.alpha_composite(img.convert("RGBA"), glow)

def slide(b, s, W, H, idx, total, hero=None):
    img = bg(b, W, H); d = ImageDraw.Draw(img)
    pad = 90
    y = 110 if (hero and idx == 0) else (int(H * 0.22) if H < 1500 else int(H * 0.28))
    if hero and idx == 0:
        h = Image.open(hero).convert("RGB")
        hw = W - 2 * pad; hh = int(H * 0.42)
        r = max(hw / h.width, hh / h.height); h = h.resize((int(h.width * r), int(h.height * r)))
        h = h.crop(((h.width - hw) // 2, (h.height - hh) // 2, (h.width - hw) // 2 + hw, (h.height - hh) // 2 + hh))
        m = Image.new("L", (hw, hh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, hw, hh], radius=36, fill=255)
        img.paste(h, (pad, y), m); y += hh + 60
    if s.get("eyebrow"):
        d.text((pad, y), s["eyebrow"].upper(), font=ImageFont.truetype(BOLD, 30), fill=b["glow"]); y += 60
    if s.get("num"):
        d.text((pad, y), s["num"], font=ImageFont.truetype(BOLD, 150), fill=b["accent"]); y += 180
    size = 84 if len(s.get("title", "")) < 40 else 68
    tf = ImageFont.truetype(BOLD, size)
    for line in wrap(d, s.get("title", ""), tf, W - 2 * pad):
        d.text((pad, y), line, font=tf, fill=b["text"]); y += int(size * 1.18)
    if s.get("body"):
        y += 30; bf = ImageFont.truetype(REG, 42)
        for line in wrap(d, s["body"], bf, W - 2 * pad):
            d.text((pad, y), line, font=bf, fill=b["muted"]); y += 62
    if s.get("cta"):
        cf = ImageFont.truetype(BOLD, 46); tw = d.textlength(s["cta"], font=cf)
        y = max(y + 50, H - 330)
        d.rounded_rectangle([pad, y, pad + tw + 80, y + 104], radius=52, fill=b["accent"])
        d.text((pad + 40, y + 24), s["cta"], font=cf, fill=(20, 16, 6))
    f = ImageFont.truetype(BOLD, 28)
    d.text((pad, H - 110), b["name"] + "  ·  " + b["tag"], font=f, fill=b["muted"])
    if total > 1:
        for i in range(total):
            x = W - pad - (total - i) * 34
            d.rounded_rectangle([x, H - 100, x + 22, H - 90], radius=5, fill=b["accent"] if i == idx else b["panel"])
    return img.convert("RGB")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); b = B[spec["brand"]]
    W, H = (1080, 1350) if spec["kind"] == "carousel" else (1080, 1920)
    for i, s in enumerate(spec["slides"]):
        slide(b, s, W, H, i, len(spec["slides"]) if spec["kind"] == "carousel" else 1, spec.get("hero")).save(f"{sys.argv[2]}_{i + 1}.jpg", quality=92)
