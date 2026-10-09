"""Recorte circular, cor do contorno e dimensionamento físico (mm -> px via DPI)."""
import math
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

RING_MM = 5  # contorno: 5 mm por lado => total = arte + 10 mm

# ---------- upscale ----------
UP_MODES = {"Nenhum": "none", "Suave (Lanczos + nitidez)": "suave",
            "Alta qualidade (multi-etapas)": "alta", "IA (modelo local)": "ia"}
MODELS_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                          else os.path.dirname(os.path.abspath(__file__)), "models")
_sr = {}  # cache dos modelos de super-resolução carregados
_MASK_CACHE = {}  # máscaras circulares reutilizadas entre bottons do mesmo tamanho


def _usm(a, amount, sigma):
    """Máscara de nitidez (unsharp) em uint8."""
    return cv2.addWeighted(a, 1 + amount, cv2.GaussianBlur(a, (0, 0), sigma), -amount, 0)


def _model_files():
    try:
        return {f.lower(): f for f in os.listdir(MODELS_DIR) if f.lower().endswith(".pb")}
    except OSError:
        return {}


def ai_available():
    """True se o OpenCV tem dnn_superres (opencv-contrib) e há ao menos um modelo .pb em ./models."""
    return hasattr(cv2, "dnn_superres") and bool(_model_files())


def _ai_step(rgb, n):
    """Amplia n× (2 ou 4) com o melhor modelo disponível (EDSR > FSRCNN > ESPCN). None se não houver."""
    if not hasattr(cv2, "dnn_superres"):
        return None
    files = _model_files()
    for name in ("edsr", "fsrcnn", "espcn"):
        fn = files.get(f"{name}_x{n}.pb")
        if not fn:
            continue
        try:
            if (name, n) not in _sr:
                sr = cv2.dnn_superres.DnnSuperResImpl_create()
                sr.readModel(os.path.join(MODELS_DIR, fn))
                sr.setModel(name, n)
                _sr[(name, n)] = sr
            out = _sr[(name, n)].upsample(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        except cv2.error:
            continue
    return None


def upscale(img, d, mode="none"):
    """img (PIL RGB, quadrada) -> PIL RGB d x d. Só amplia de verdade se d > largura de img."""
    w = img.width
    if mode == "none" or d <= w * 1.05:
        return img.resize((d, d), Image.LANCZOS)
    arr = np.ascontiguousarray(np.asarray(img.convert("RGB")))
    cur = arr
    if mode == "ia":
        for _ in range(3):
            if cur.shape[1] >= d or cur.shape[1] * 2 > 6000:
                break
            n = 4 if d / cur.shape[1] > 2.5 and cur.shape[1] * 4 <= 6000 else 2
            out = _ai_step(cur, n)
            if out is None:
                break
            cur = out
        if cur is arr:
            mode = "alta"  # sem modelo: cai para o método clássico
        else:
            return Image.fromarray(cur).resize((d, d), Image.LANCZOS)
    if mode == "alta":
        cur = cv2.fastNlMeansDenoisingColored(arr, None, 3, 3, 5, 15)  # tira ruído/artefatos de JPEG
        while cur.shape[1] < d:  # passos de até 2× com nitidez leve a cada etapa
            nw = min(d, cur.shape[1] * 2)
            cur = _usm(cv2.resize(cur, (nw, nw), interpolation=cv2.INTER_LANCZOS4), 0.5, 1.0)
        return Image.fromarray(cur)
    cur = cv2.resize(arr, (d, d), interpolation=cv2.INTER_LANCZOS4)  # "suave"
    return Image.fromarray(_usm(cur, 0.4, 1.0))



# ---------- abertura da folha ----------
MAX_SHEET_PIXELS = 100_000_000   # folha maior que isso é reduzida ao abrir (≈ 10.000 × 10.000 px); abaixo disso nada muda


def open_sheet(path, max_px=MAX_SHEET_PIXELS):
    """Abre a folha de bottons como RGB. Devolve (imagem, (largura_original, altura_original)).
    Se a folha era grande demais, a imagem devolvida é menor que o original (reduzida por média de blocos,
    sem perder nitidez); senão o tamanho é o mesmo.

    Por que reduzir: uma folha de centenas de milhões de pixels é bloqueada pelo Pillow ("decompression bomb")
    e, mesmo liberada, o programa faz várias cópias dela na memória (RGB, NumPy, BGR, float32) e passaria de
    10 GB. A arte de cada botton continua com muito mais pixels do que a impressão precisa (um botton de 42 mm
    a 300 DPI tem só ~500 px). O limite anti-bomba do Pillow é desligado só durante a abertura: o arquivo foi
    escolhido por você e é reduzido na hora. Para manter mais detalhe, aumente MAX_SHEET_PIXELS."""
    old = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    try:
        im = Image.open(path)
        w0, h0 = im.size
        if im.format == "JPEG" and w0 * h0 > max_px:
            f = math.ceil(math.sqrt(w0 * h0 / max_px))   # JPEG decodifica direto em 1/2, 1/4 ou 1/8: rápido e leve
            im.draft("RGB", (math.ceil(w0 / f), math.ceil(h0 / f)))
        im.load()
        if im.mode not in ("RGB", "L"):   # RGBA, paleta, 16 bits...: vira RGB (a transparência é descartada, como sempre foi)
            im = im.convert("RGB")        # e o reduce() abaixo não precisa de uma cópia extra em 4 bytes por pixel
        f = max(1, math.ceil(math.sqrt(im.width * im.height / max_px)))
        if f > 1:
            im = im.reduce(f)   # reduz ANTES de converter: a cópia convertida já nasce pequena
        im = im.convert("RGB")
    finally:
        Image.MAX_IMAGE_PIXELS = old
    return im, (w0, h0)


def mm(v, dpi):
    return round(v / 25.4 * dpi)


def disc_mask(d):
    """Máscara circular com antialiasing (supersampling 4x), com cache por tamanho."""
    d = int(d)
    cached = _MASK_CACHE.get(d)
    if cached is not None:
        return cached
    S = 4
    m = Image.new("L", (d * S, d * S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * S - 1, d * S - 1), fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    _MASK_CACHE[d] = m
    # Evita crescimento ilimitado caso o programa receba muitos tamanhos customizados.
    if len(_MASK_CACHE) > 64:
        _MASK_CACHE.pop(next(iter(_MASK_CACHE)))
    return m


def edge_color(src, cx, cy, r):
    """Cor dominante da faixa externa da arte (k-means na borda)."""
    x0, y0 = max(0, int(cx - r)), max(0, int(cy - r))
    x1, y1 = min(src.width, int(cx + r) + 1), min(src.height, int(cy + r) + 1)
    a = np.asarray(src.crop((x0, y0, x1, y1)).convert("RGB"))   # só a região do botton (não a folha inteira)
    yy, xx = np.ogrid[:a.shape[0], :a.shape[1]]
    d = np.hypot(xx + x0 - cx, yy + y0 - cy)
    px = a[(d > .86 * r) & (d < .97 * r)].astype(np.float32)
    if len(px) < 10:
        return (255, 255, 255)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lab, cen = cv2.kmeans(px, 3, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    return tuple(int(v) for v in cen[np.bincount(lab.ravel()).argmax()])


def art_circle(src, cx, cy, r, rot, d, up="none"):
    """Recorta o círculo (sem deformar: caixa quadrada), gira e reamostra p/ d px."""
    side = int(2 * r * 1.6)
    box = (int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2))
    fill = tuple(edge_color(src, cx, cy, r))
    t = Image.new("RGB", (side, side), fill)  # fora da imagem: cor da borda (nunca preto)
    t.paste(src, (-box[0], -box[1]))
    t = t.rotate(-rot, resample=Image.BICUBIC, fillcolor=fill)
    inner = int(2 * r)
    o = (side - inner) // 2
    t = upscale(t.crop((o, o, o + inner, o + inner)), d, up)
    return t.convert("RGBA")


def make_button(src, cx, cy, r, art_mm, dpi, color, rot=0, up="none"):
    """Botton final RGBA: arte (art_mm) + contorno de 5 mm por lado."""
    ring = mm(RING_MM, dpi)
    total = mm(art_mm + 2 * RING_MM, dpi)
    art = total - 2 * ring  # garante diferença radial exata de 5 mm
    out = Image.new("RGBA", (total, total), tuple(color) + (255,))
    out.putalpha(disc_mask(total))
    a = art_circle(src, cx, cy, r, rot, art, up)
    a.putalpha(disc_mask(art))
    out.alpha_composite(a, (ring, ring))
    return out


def trim_margin(src, cx, cy, r, n=240, m=140):
    """Se houver margem clara/vazia em volta da arte, devolve (cx, cy, r) ajustados à arte."""
    from detect import _fit
    rs = np.linspace(0.5 * r, r, m)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    mx = (cx + rs[None] * np.cos(a)[:, None]).astype(np.float32)
    my = (cy + rs[None] * np.sin(a)[:, None]).astype(np.float32)
    # só a região do botton vira float32 (a folha inteira, em folhas enormes, ocuparia GBs a cada botton)
    bx0, by0 = max(0, int(np.floor(cx - r)) - 2), max(0, int(np.floor(cy - r)) - 2)
    bx1, by1 = min(src.width, int(np.ceil(cx + r)) + 3), min(src.height, int(np.ceil(cy + r)) + 3)
    roi = np.asarray(src.crop((bx0, by0, bx1, by1)).convert("RGB"), dtype=np.float32)
    prof = cv2.remap(roi, mx - bx0, my - by0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ref = np.median(prof[:, -4:].reshape(-1, 3), axis=0)  # cor da faixa externa
    if ref.min() < 200 or ref.max() - ref.min() > 45:  # só trata margem clara/neutra
        return cx, cy, r
    nb = np.linalg.norm(prof - ref, axis=2) > 28
    nb[:, -int(m * 0.06):] = False
    nb = nb & np.roll(nb, 1, 1) & np.roll(nb, 2, 1)  # ignora pontinhos isolados
    has = nb.any(axis=1)
    if has.sum() < n * 0.5:
        return cx, cy, r
    idx = (m - 1 - nb[:, ::-1].argmax(axis=1))[has]  # pixel de arte mais externo em cada direção
    k = np.arange(n)[has]
    pts = np.c_[mx[k, idx], my[k, idx]]
    for _ in range(4):
        fx, fy, fr = _fit(pts)
        res = np.abs(np.hypot(pts[:, 0] - fx, pts[:, 1] - fy) - fr)
        keep = res < max(2 * np.median(res), 0.01 * fr)
        if keep.sum() < 20:
            return cx, cy, r
        pts = pts[keep]
    fx, fy, fr = _fit(pts)
    if not (0.5 * r < fr < 0.96 * r) or np.hypot(fx - cx, fy - cy) > 0.2 * r:
        return cx, cy, r  # sem margem relevante (<4%): mantém
    return fx, fy, fr * 1.005


def auto_color(src, cx, cy, r):
    """Cor do contorno calculada na borda da arte."""
    a = art_circle(src, cx, cy, r, 0, 256)
    return edge_color(a.convert("RGB"), 128, 128, 126)
