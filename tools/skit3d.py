"""3D blocky-character skit reel: a human with a problem + a helper character (Jarvis or Casa).
spec: {"brand":"jarvis"|"azure","time":"3:12 AM","human":{"name":"Mike","voice":"am_adam","shirt":[r,g,b],"hair":[r,g,b],"skin":[r,g,b],"style":"short"|"long"},
       "beats":[{"who":"human"|"helper","say":"...","mood":"sad"|"happy"|"neutral"|"shock"}],"cta":"DM \"BUILD\"","cta_sub":"..."}
usage: PYOPENGL_PLATFORM=egl python3 skit3d.py spec.json out.mp4
"""
import os, sys, json, math, random, subprocess
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np, soundfile as sf, trimesh, pyrender
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

RW, RH, W, H, FPS, SR = 540, 960, 1080, 1920, 30, 24000
TTS = os.environ.get("TTS_DIR", "/home/claude/tts")
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
BR = {
    "jarvis": dict(helper="jarvis", hvoice="bm_george", hname="JARVIS", tag="@jarvisworks.ai", accent=(255, 181, 71), glow=(76, 201, 255),
                   bg=[0.03, 0.05, 0.14, 1], wall=(22, 30, 70)),
    "azure": dict(helper="casa", hvoice="af_heart", hname="CASA", tag="@azure.cashoffers", accent=(255, 200, 87), glow=(63, 169, 245),
                  bg=[0.04, 0.10, 0.22, 1], wall=(28, 52, 92)),
}

_k = None
def tts(text, voice, speed=1.0):
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(f"{TTS}/kokoro-v1.0.onnx", f"{TTS}/voices-v1.0.bin")
    s, _ = _k.create(text, voice=voice, speed=speed, lang="en-us")
    return s.astype(np.float32)

def mat(rgb, emissive=0.0, rough=0.8):
    c = [x / 255 for x in rgb]
    return pyrender.MetallicRoughnessMaterial(baseColorFactor=c + [1], metallicFactor=0.0, roughnessFactor=rough,
                                              emissiveFactor=[x * emissive for x in c])

def box(scene, size, pos, rgb, parent=None, emissive=0.0):
    m = pyrender.Mesh.from_trimesh(trimesh.creation.box(size), material=mat(rgb, emissive), smooth=False)
    T = np.eye(4); T[:3, 3] = pos
    n = pyrender.Node(mesh=m, matrix=T)
    scene.add_node(n, parent_node=parent)
    return n

def group(scene, pos, parent=None):
    T = np.eye(4); T[:3, 3] = pos
    n = pyrender.Node(matrix=T); scene.add_node(n, parent_node=parent); return n

def setT(node, pos=None, scale=None, rotz=0.0, roty=0.0):
    T = np.eye(4)
    cz, sz, cy, sy = math.cos(rotz), math.sin(rotz), math.cos(roty), math.sin(roty)
    R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    S = np.diag(scale if scale is not None else [1, 1, 1])
    T[:3, :3] = R @ S
    T[:3, 3] = pos
    node.matrix = T

# ---------------- characters ----------------
def build_human(scene, x, h):
    skin, shirt, hair = h.get("skin", [236, 196, 160]), h.get("shirt", [240, 200, 60]), h.get("hair", [60, 40, 30])
    root = group(scene, [x, 0, 0])
    P = {"root": root, "base": [x, 0, 0]}
    for sx in (-0.17, 0.17): box(scene, (0.3, 0.9, 0.32), [sx, 0.45, 0], [40, 50, 80], root)
    P["torso"] = box(scene, (0.8, 0.9, 0.42), [0, 1.35, 0], shirt, root)
    P["arms"] = [box(scene, (0.26, 0.85, 0.3), [sx, 1.33, 0], shirt, root) for sx in (-0.54, 0.54)]
    for sx in (-0.54, 0.54): box(scene, (0.24, 0.2, 0.28), [sx, 0.85, 0], skin, root)
    head = group(scene, [0, 2.2, 0], root); P["head"] = head
    box(scene, (0.78, 0.78, 0.78), [0, 0, 0], skin, head)
    rnd = random.Random(7)
    if h.get("style", "short") == "long":
        box(scene, (0.86, 0.22, 0.86), [0, 0.45, 0], hair, head)
        box(scene, (0.86, 0.8, 0.2), [0, 0.05, -0.38], hair, head)
        for sx in (-0.42, 0.42): box(scene, (0.12, 0.85, 0.7), [sx, 0.02, -0.05], hair, head)
        box(scene, (0.8, 0.14, 0.12), [0, 0.33, 0.4], hair, head)
    else:
        for i in range(6):
            bx = -0.3 + i * 0.12
            box(scene, (0.2, 0.18 + rnd.random() * 0.14, 0.6), [bx, 0.45 + rnd.random() * 0.05, -0.05], hair, head)
        box(scene, (0.84, 0.14, 0.2), [0, 0.36, 0.36], hair, head)
    P["eyes"] = [box(scene, (0.11, 0.13, 0.02), [sx, 0.06, 0.4], [25, 20, 25], head) for sx in (-0.17, 0.17)]
    for sx in (-0.15, 0.19): box(scene, (0.03, 0.03, 0.01), [sx, 0.09, 0.415], [255, 255, 255], head)
    P["brows"] = [box(scene, (0.2, 0.05, 0.02), [sx, 0.2, 0.4], [40, 28, 22], head) for sx in (-0.17, 0.17)]
    box(scene, (0.08, 0.1, 0.06), [0, -0.05, 0.42], [220, 175, 140], head)  # nose
    P["mouth"] = box(scene, (0.24, 0.05, 0.02), [0, -0.2, 0.4], [70, 30, 35], head)
    return P

def build_jarvis(scene, x, b):
    g = b["glow"]
    root = group(scene, [x, 2.1, 0.2]); P = {"root": root, "base": [x, 2.1, 0.2]}
    box(scene, (0.9, 0.8, 0.8), [0, 0, 0], [16, 28, 52], root)
    box(scene, (0.94, 0.06, 0.84), [0, 0.42, 0], g, root, emissive=1.0)
    box(scene, (0.74, 0.34, 0.04), [0, 0.06, 0.41], [4, 8, 18], root)
    P["eyes"] = [box(scene, (0.16, 0.16, 0.03), [sx, 0.06, 0.43], g, root, emissive=1.4) for sx in (-0.18, 0.18)]
    P["mouth"] = [box(scene, (0.05, 0.05, 0.03), [-0.15 + i * 0.075, -0.24, 0.42], b["accent"], root, emissive=1.2) for i in range(5)]
    box(scene, (0.05, 0.3, 0.05), [0, 0.6, 0], [120, 140, 170], root)
    box(scene, (0.12, 0.12, 0.12), [0, 0.8, 0], b["accent"], root, emissive=1.5)
    for sx in (-0.5, 0.5): box(scene, (0.1, 0.3, 0.3), [sx, 0, 0], g, root, emissive=0.6)
    return P

def build_casa(scene, x, b):
    root = group(scene, [x, 1.7, 0.1]); P = {"root": root, "base": [x, 1.7, 0.1]}
    box(scene, (1.1, 0.95, 0.9), [0, 0, 0], [242, 246, 255], root)
    v = np.array([[-0.7, 0.47, -0.5], [0.7, 0.47, -0.5], [0, 1.05, -0.5], [-0.7, 0.47, 0.5], [0.7, 0.47, 0.5], [0, 1.05, 0.5]])
    f = np.array([[0, 2, 1], [3, 4, 5], [0, 1, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 2, 5], [1, 5, 4]])
    roof = trimesh.Trimesh(v, f); roof.fix_normals()
    scene.add_node(pyrender.Node(mesh=pyrender.Mesh.from_trimesh(roof, material=mat(b["accent"]), smooth=False)), parent_node=root)
    box(scene, (0.16, 0.36, 0.16), [0.32, 0.95, 0], [220, 120, 70], root)
    for sx in (-0.26, 0.26): box(scene, (0.3, 0.26, 0.02), [sx, 0.15, 0.46], b["glow"], root, emissive=0.4)
    P["eyes"] = [box(scene, (0.11, 0.15, 0.02), [sx, 0.15, 0.475], [11, 37, 69], root) for sx in (-0.26, 0.26)]
    for sx in (-0.39, 0.39): box(scene, (0.12, 0.06, 0.01), [sx, -0.06, 0.46], [255, 160, 160], root)
    P["mouth"] = box(scene, (0.26, 0.1, 0.02), [0, -0.26, 0.47], [11, 37, 69], root)
    return P

def build_set(scene, b, kind="home_office"):
    G = lambda c, k=0.7: tuple(int(x * k) for x in c)
    walls = {"home_office": (70, 78, 110), "clinic": (170, 215, 215), "garage": (120, 110, 95), "kitchen_leak": (215, 195, 160),
             "living_boxes": (165, 140, 120), "rental_damage": (190, 185, 170)}
    floors = {"home_office": (110, 80, 60), "clinic": (225, 228, 230), "garage": (90, 90, 95), "kitchen_leak": (180, 170, 150),
              "living_boxes": (120, 85, 60), "rental_damage": (140, 120, 100)}
    w = walls.get(kind, b["wall"]); fl = floors.get(kind, G(w))
    box(scene, (14, 9, 0.2), [0, 3.5, -1.6], w)
    box(scene, (14, 0.2, 8), [0, -0.1, 1.0], fl)
    box(scene, (14, 0.25, 0.1), [0, 0.12, -1.48], G(w, 0.6))  # baseboard
    def window(x, y, night=True):
        box(scene, (1.5, 1.15, 0.05), [x, y, -1.48], (14, 20, 55) if night else (150, 200, 240), emissive=0.35)
        if night: box(scene, (0.2, 0.2, 0.05), [x + 0.4, y + 0.25, -1.45], (250, 245, 210), emissive=1.2)
        box(scene, (1.62, 0.07, 0.09), [x, y, -1.44], (235, 235, 240)); box(scene, (0.07, 1.25, 0.09), [x, y, -1.44], (235, 235, 240))
    def frame(x, y, c): box(scene, (0.5, 0.4, 0.05), [x, y, -1.47], (60, 45, 35)); box(scene, (0.4, 0.3, 0.06), [x, y, -1.46], c, emissive=0.15)
    if kind == "home_office":
        window(-1.9, 2.9)
        box(scene, (1.6, 0.08, 0.7), [1.9, 1.0, -0.7], (120, 80, 50)); box(scene, (0.08, 1.0, 0.6), [2.6, 0.5, -0.7], (100, 66, 40))
        box(scene, (0.62, 0.42, 0.04), [1.7, 1.3, -0.9], b["glow"], emissive=0.9); box(scene, (0.7, 0.03, 0.4), [1.7, 1.06, -0.75], (60, 60, 70))
        for i in range(3):
            box(scene, (1.3, 0.06, 0.3), [1.9, 2.4 + i * 0.5, -1.4], (110, 75, 50))
            for j in range(5): box(scene, (0.12, 0.35, 0.22), [1.4 + j * 0.2, 2.6 + i * 0.5, -1.4], [(200, 60, 60), (60, 120, 200), (230, 190, 70), (80, 160, 100), (180, 180, 190)][(i + j) % 5])
        box(scene, (0.3, 0.35, 0.3), [-2.6, 0.18, -0.9], (180, 90, 60)); box(scene, (0.5, 0.6, 0.5), [-2.6, 0.7, -0.9], (60, 150, 80))
        box(scene, (0.18, 0.18, 0.12), [2.2, 1.12, -0.8], (240, 240, 240))  # mug
    elif kind == "clinic":
        window(-2.1, 3.0, night=False)
        box(scene, (1.2, 0.5, 0.7), [2.0, 0.6, -0.9], (60, 170, 170)); box(scene, (0.5, 1.0, 0.7), [2.45, 1.2, -0.9], (60, 170, 170))
        box(scene, (0.3, 0.9, 0.3), [1.6, 0.45, -0.9], (200, 205, 210)); box(scene, (0.5, 0.06, 0.4), [1.4, 1.5, -0.7], (230, 230, 235))
        box(scene, (0.6, 0.6, 0.05), [0.2, 3.4, -1.47], (255, 255, 255)); box(scene, (0.04, 0.22, 0.06), [0.2, 3.47, -1.44], (40, 40, 40)); box(scene, (0.18, 0.04, 0.06), [0.27, 3.4, -1.44], (40, 40, 40))
        box(scene, (0.8, 1.1, 0.05), [-1.2, 2.6, -1.47], (255, 255, 255)); [box(scene, (0.6, 0.05, 0.06), [-1.2, 3.0 - i * 0.18, -1.44], (80, 140, 200)) for i in range(4)]
        box(scene, (2.0, 0.08, 0.3), [-2.2, 0.15, -0.2], (60, 170, 170))
    elif kind == "garage":
        box(scene, (3.0, 1.6, 0.05), [0.5, 2.6, -1.47], (175, 145, 105))  # pegboard
        for i in range(7): box(scene, (0.08, 0.5 + (i % 3) * 0.15, 0.06), [-0.7 + i * 0.4, 2.7, -1.43], [(200, 50, 40), (60, 60, 70), (230, 180, 40)][i % 3])
        for i in range(8): box(scene, (0.07, 0.07, 0.4), [-2.3, 0.2 + i * 0.4, -1.1], (200, 200, 205))  # ladder rungs
        for x in (-2.55, -2.05): box(scene, (0.08, 3.4, 0.08), [x, 1.6, -1.1], (200, 200, 205))
        box(scene, (1.6, 0.9, 0.7), [2.1, 0.45, -1.0], (200, 50, 40)); box(scene, (1.6, 0.08, 0.72), [2.1, 0.92, -1.0], (60, 60, 65))
        for i in range(4): box(scene, (1.0, 0.1, 0.6), [2.1, 1.0 + i * 0.11, -1.0], (70, 70, 80) if i % 2 else (90, 85, 85))  # shingles
        box(scene, (0.5, 0.35, 0.3), [-1.5, 0.18, -0.6], (230, 180, 40))
        box(scene, (6, 0.2, 0.05), [0, 4.6, -1.46], (255, 240, 200), emissive=0.4)
    elif kind == "kitchen_leak":
        for i in range(4): box(scene, (0.62, 0.9, 0.6), [0.9 + i * 0.66, 0.45, -1.2], (240, 240, 235)); box(scene, (0.62, 0.7, 0.4), [0.9 + i * 0.66, 2.8, -1.35], (240, 240, 235))
        box(scene, (2.7, 0.08, 0.66), [1.9, 0.94, -1.2], (90, 80, 75))
        box(scene, (0.9, 2.2, 0.7), [-2.1, 1.1, -1.1], (220, 225, 230)); box(scene, (0.05, 0.5, 0.05), [-1.75, 1.6, -0.74], (150, 150, 155))
        box(scene, (1.2, 0.04, 0.8), [0.2, 4.3, -0.8], (150, 120, 70))  # ceiling stain hint
        box(scene, (0.35, 0.4, 0.35), [0.25, 0.2, 0.3], (120, 160, 200)); box(scene, (0.3, 0.05, 0.3), [0.25, 0.38, 0.3], (60, 120, 200), emissive=0.4)
        box(scene, (1.0, 0.35, 0.05), [-0.4, 3.1, -1.47], (150, 115, 70))  # water stain on wall
        window(-0.3, 2.4)
    elif kind == "living_boxes":
        box(scene, (2.0, 0.5, 0.9), [2.0, 0.45, -0.9], (120, 90, 140)); box(scene, (2.0, 0.6, 0.25), [2.0, 0.95, -1.25], (120, 90, 140))
        for (x, y, z, c) in [(-2.0, 0.25, -0.9, (190, 150, 100)), (-2.0, 0.75, -0.9, (175, 138, 92)), (-1.5, 0.25, -0.7, (190, 150, 100)),
                             (-2.05, 1.22, -0.95, (200, 160, 110)), (-1.4, 0.75, -0.75, (180, 140, 95)), (2.7, 0.25, 0.0, (190, 150, 100))]:
            box(scene, (0.5, 0.48, 0.5), [x, y, z], c); box(scene, (0.5, 0.05, 0.12), [x, y + 0.24, z], (230, 200, 120))
        frame(-0.6, 3.0, (200, 160, 120)); frame(0.3, 3.2, (150, 180, 200)); frame(1.3, 2.9, (220, 190, 150))
        box(scene, (0.1, 1.6, 0.1), [-2.6, 0.8, -1.2], (60, 50, 40)); box(scene, (0.5, 0.4, 0.5), [-2.6, 1.75, -1.2], (250, 230, 170), emissive=0.7)
        window(0.4, 2.0)
    elif kind == "rental_damage":
        for (x, y, sx, sy) in [(-1.2, 1.4, 0.3, 0.25), (0.6, 2.4, 0.22, 0.3), (1.6, 1.1, 0.35, 0.2), (-0.2, 3.1, 0.25, 0.2)]:
            box(scene, (sx, sy, 0.05), [x, y, -1.47], (40, 35, 35))
        box(scene, (1.4, 0.02, 1.0), [1.2, 0.01, 0.2], (90, 70, 50)); box(scene, (0.9, 0.02, 0.7), [-1.6, 0.01, -0.3], (100, 80, 55))
        for (x, z) in [(2.2, -0.8), (2.6, -0.4), (-2.3, -0.9)]: box(scene, (0.45, 0.55, 0.45), [x, 0.27, z], (30, 30, 35))
        window(-2.0, 2.8, night=False)
        box(scene, (0.05, 1.8, 0.9), [2.9, 0.9, -0.6], (150, 110, 70))
    light_c = {"clinic": (1, 1, 1), "garage": (1, 0.95, 0.85)}.get(kind, (1, 0.9, 0.78))
    return light_c

def look_at(eye, target):
    f = np.array(target) - np.array(eye); f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = r, u, -f, eye
    return M

def wrap(d, words, font, maxw):
    rows, cur = [], []
    for i, w in enumerate(words):
        test = " ".join(x for _, x in cur + [(i, w)])
        if cur and d.textlength(test, font=font) > maxw: rows.append(cur); cur = [(i, w)]
        else: cur.append((i, w))
    if cur: rows.append(cur)
    return rows

def render(spec, out):
    b = BR[spec["brand"]]; hu = spec["human"]
    # ---- audio ----
    pos, segs, clips = int(0.5 * SR), [], []
    for bt in spec["beats"]:
        voice = hu["voice"] if bt["who"] == "human" else b["hvoice"]
        a = tts(bt["say"], voice, bt.get("speed", 1.0))
        segs.append(dict(t0=pos / SR, t1=(pos + len(a)) / SR, **bt)); clips.append((pos, a, bt["who"]))
        pos += len(a) + int(0.3 * SR)
    cta_t = pos / SR; total = cta_t + 2.8
    N = int(total * SR)
    voice = {"human": np.zeros(N, np.float32), "helper": np.zeros(N, np.float32)}
    for p, a, who in clips: voice[who][p:p + len(a)] += a[: N - p]
    tt = np.arange(N) / SR
    music = 0.02 * (np.sin(2 * np.pi * 220 * tt) * (np.sin(2 * np.pi * 2 * tt) > 0) + 0.7 * np.sin(2 * np.pi * 110 * tt))
    audio = voice["human"] + voice["helper"] + music.astype(np.float32)
    wav = out + ".wav"; sf.write(wav, audio, SR)
    hop = SR // FPS
    def envelope(v):
        e = np.array([np.sqrt(np.mean(v[i:i + hop] ** 2)) for i in range(0, len(v), hop)])
        return np.clip(e / (e.max() + 1e-6) * 1.8, 0, 1)
    env = {k: envelope(v) for k, v in voice.items()}

    # ---- scene ----
    scene = pyrender.Scene(bg_color=b["bg"], ambient_light=[0.12, 0.12, 0.16])
    light_c = build_set(scene, b, spec.get("set", "home_office"))
    HUM = build_human(scene, -0.55, hu)
    HEL = (build_jarvis if b["helper"] == "jarvis" else build_casa)(scene, 0.95, b)
    key = pyrender.DirectionalLight(color=list(light_c), intensity=1.9)
    scene.add(key, pose=look_at([2, 5, 6], [0, 1.5, 0]))
    rim = pyrender.PointLight(color=[c / 255 for c in b["glow"]], intensity=5.0)
    scene.add(rim, pose=look_at([1.5, 3, 1.5], [0, 2, 0]))
    cam = pyrender.PerspectiveCamera(yfov=math.radians(42), aspectRatio=RW / RH)
    cnode = scene.add(cam, pose=np.eye(4))
    R = pyrender.OffscreenRenderer(RW, RH)

    cap = ImageFont.truetype(BOLD, 70); big = ImageFont.truetype(BOLD, 96); small = ImageFont.truetype(BOLD, 36); tagf = ImageFont.truetype(BOLD, 30)
    rnd = random.Random(spec.get("seed", 2))
    blinks = set(); tb = 0.8
    while tb < total: blinks.update(range(int(tb * FPS), int(tb * FPS) + 4)); tb += rnd.uniform(2.0, 3.8)
    bokeh = [(rnd.uniform(0, W), rnd.uniform(0, 900), rnd.uniform(10, 34), rnd.uniform(0, 6.28)) for _ in range(22)]

    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    camE, camT = np.array([0.2, 2.2, 5.0]), np.array([0.2, 1.8, 0])
    nF = int(total * FPS)
    for fr in range(nF):
        t = fr / FPS
        seg = next((s for s in segs if s["t0"] - 0.15 <= t < s["t1"] + 0.3), None)
        in_cta = t >= cta_t
        mh = float(env["human"][min(fr, len(env["human"]) - 1)]); mj = float(env["helper"][min(fr, len(env["helper"]) - 1)])
        mood = seg["mood"] if seg and seg["who"] == "human" else (spec["beats"][-1].get("mood", "happy") if in_cta else "neutral")
        if seg is None and not in_cta:
            prev = [s for s in segs if s["t1"] <= t]; mood = prev[-1]["mood"] if prev and prev[-1]["who"] == "human" else mood
        # human pose
        breathe = 0.02 * math.sin(t * 2.5)
        setT(HUM["root"], [HUM["base"][0], breathe, 0])
        tilt = {"sad": -0.12, "shock": 0.0, "happy": 0.08, "neutral": 0.0}.get(mood, 0)
        nod = 0.05 * math.sin(t * 9) * mh
        setT(HUM["head"], [0, 2.2, 0], rotz=tilt * 0.5 + nod, roty=0.25 + 0.05 * math.sin(t))
        blink = fr in blinks
        eh = 0.12 if blink else (1.5 if mood == "shock" else 1.0)
        for i, e in enumerate(HUM["eyes"]): setT(e, [(-0.17, 0.17)[i], 0.06, 0.4], [1, eh, 1])
        br = {"sad": 0.35, "shock": 0.0, "happy": -0.1, "neutral": 0.0}.get(mood, 0)
        by = 0.25 if mood == "shock" else 0.2
        for i, e in enumerate(HUM["brows"]): setT(e, [(-0.17, 0.17)[i], by, 0.4], rotz=(br if i == 0 else -br))
        mw = 1.3 if mood == "happy" else (0.7 if mood == "sad" else 1.0)
        setT(HUM["mouth"], [0, -0.2, 0.4], [mw, 1 + mh * 3.5 + (1.5 if mood == "shock" else 0), 1])
        sw = 0.15 * math.sin(t * 6) * mh
        for i, a in enumerate(HUM["arms"]): setT(a, [(-0.54, 0.54)[i], 1.33, 0], rotz=(sw if i == 0 else -sw))
        # helper pose
        hb = HEL["base"]; first_h = next((x["t0"] for x in segs if x["who"] == "helper"), 0); arrive = min(1, max(0, (t - first_h + 0.9) / 0.8))
        hx = hb[0] + (1 - arrive) * 2.5
        setT(HEL["root"], [hx, hb[1] + 0.08 * math.sin(t * 2.2) + mj * 0.04, hb[2]], roty=-0.3 + 0.1 * math.sin(t * 1.3), rotz=0.04 * math.sin(t * 1.7))
        ehj = 0.15 if blink else 1.0
        if b["helper"] == "jarvis":
            for i, e in enumerate(HEL["eyes"]): setT(e, [(-0.18, 0.18)[i], 0.06, 0.43], [1, ehj, 1])
            for i, m in enumerate(HEL["mouth"]):
                hh = 1 + mj * 5 * (0.5 + 0.5 * math.sin(t * 20 + i * 1.4)) * (1 - abs(i - 2) / 4)
                setT(m, [-0.15 + i * 0.075, -0.24, 0.42], [1, hh, 1])
        else:
            for i, e in enumerate(HEL["eyes"]): setT(e, [(-0.26, 0.26)[i], 0.15, 0.475], [1, ehj, 1])
            setT(HEL["mouth"], [0, -0.26, 0.47], [1 + mj * 0.3, 1 + mj * 3.5, 1])
        # camera: favour whoever talks, push in slowly
        if in_cta: tgtE, tgtT = np.array([0.2, 2.4, 5.6]), np.array([0.2, 1.7, 0])
        elif seg and seg["who"] == "human": tgtE, tgtT = np.array([-0.1, 2.3, 5.2]), np.array([0.0, 1.85, 0])
        elif seg: tgtE, tgtT = np.array([0.5, 2.3, 5.2]), np.array([0.45, 1.85, 0])
        else: tgtE, tgtT = camE, camT
        camE += (tgtE - camE) * 0.08; camT += (tgtT - camT) * 0.08
        scene.set_pose(cnode, look_at(camE + [0.03 * math.sin(t * 0.7), 0.02 * math.sin(t * 1.1), 0], camT))
        col, _ = R.render(scene)
        img = ImageEnhance.Color(ImageEnhance.Contrast(Image.fromarray(col)).enhance(1.15)).enhance(1.45).resize((W, H), Image.BICUBIC)
        # bokeh overlay
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for bx, by_, br_, ph in bokeh:
            a = int(40 + 30 * math.sin(t * 1.5 + ph)); c = b["glow"] if ph > 3 else b["accent"]
            od.ellipse([bx - br_, by_ - br_, bx + br_, by_ + br_], fill=c + (a,))
        ov = ov.filter(ImageFilter.GaussianBlur(6))
        img = Image.alpha_composite(img.convert("RGBA"), ov)
        # bottom gradient for captions
        grad = Image.new("L", (1, H)); grad.putdata([0 if y < 1150 else min(210, int((y - 1150) * 0.5)) for y in range(H)])
        img = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, grad.resize((W, H)))
        d = ImageDraw.Draw(img)
        # time chip
        if spec.get("time") and 3.2 <= t < 7:
            tw = d.textlength(spec["time"], font=tagf)
            d.rounded_rectangle([W / 2 - tw / 2 - 26, 150, W / 2 + tw / 2 + 26, 210], radius=14, fill=(0, 0, 0, 150), outline=(255, 255, 255, 60))
            d.text((W / 2 - tw / 2, 160), spec["time"], font=tagf, fill=(240, 240, 245))
        if spec.get("hook") and t < 3.2:
            e = min(1, t / 0.3); hf = ImageFont.truetype(BOLD, 82)
            hrows = wrap(d, spec["hook"].split(), hf, W - 120)
            for ri, row in enumerate(hrows):
                tx = " ".join(w for _, w in row)
                d.text(((W - d.textlength(tx, font=hf)) / 2, 260 + ri * 100 - (1 - e) * 30), tx, font=hf, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
        if seg and not in_cta:
            name = hu["name"].upper() if seg["who"] == "human" else b["hname"]
            ncol = (255, 255, 255) if seg["who"] == "human" else b["glow"]
            words = seg["say"].split()
            wts = np.cumsum([len(w) + 2 for w in words]); wts = wts / wts[-1]
            prog = (t - seg["t0"]) / max(0.05, seg["t1"] - seg["t0"])
            act = int(np.searchsorted(wts, min(0.999, max(0.0, prog))))
            if prog < 0: act = -1
            # chunk into short phrases of up to 5 words; show only the phrase being spoken, revealing word by word
            chunks, cur = [], []
            for i, w in enumerate(words):
                cur.append(i)
                if len(cur) == 5 or w[-1] in ".,?!": chunks.append(cur); cur = []
            if cur: chunks.append(cur)
            ci = next((k for k, c in enumerate(chunks) if max(0, act) in c), len(chunks) - 1)
            shown = [i for i in chunks[ci] if i <= act]
            if shown:
                rows = wrap(d, [words[i] for i in chunks[ci]], cap, W - 140)
                y0 = 1470
                d.text((70, y0 - 64), name, font=tagf, fill=ncol)
                for ri, row in enumerate(rows):
                    tx_full = " ".join(w for _, w in row)
                    x = (W - d.textlength(tx_full, font=cap)) / 2
                    for j, _ in row:
                        i = chunks[ci][j]
                        if i <= act:
                            c = b["accent"] if i == act else (255, 255, 255)
                            d.text((x, y0 + ri * 92), words[i], font=cap, fill=c, stroke_width=5, stroke_fill=(0, 0, 0))
                        x += d.textlength(words[i] + " ", font=cap)
        if in_cta:
            e = min(1, (t - cta_t) / 0.4)
            rows = wrap(d, spec["cta"].split(), big, W - 140)
            for ri, row in enumerate(rows):
                tx = " ".join(w for _, w in row)
                d.text(((W - d.textlength(tx, font=big)) / 2, 1360 + ri * 112 + (1 - e) * 40), tx, font=big, fill=b["accent"], stroke_width=5, stroke_fill=(0, 0, 0))
            sub = spec.get("cta_sub", "")
            if sub: d.text(((W - d.textlength(sub, font=small)) / 2, 1370 + len(rows) * 112 + 20), sub, font=small, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((70, H - 120), b["tag"], font=tagf, fill=(255, 255, 255, 200))
        p.stdin.write(img.convert("RGB").tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
