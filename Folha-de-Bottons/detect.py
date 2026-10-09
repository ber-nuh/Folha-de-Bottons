"""Detecção de bottons redondos: segmenta o fundo, separa bottons encostados
(transformada de distância) e valida pelo tamanho. Hough só como plano B."""
import cv2
import numpy as np

MAXSIDE = 1400


def _segment(small):
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
    b = max(3, min(small.shape[:2]) // 60)
    border = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                             lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    diff = np.linalg.norm(lab - np.median(border, axis=0), axis=2)
    d8 = np.clip(diff * 4, 0, 255).astype(np.uint8)
    t, _ = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = (d8 > max(t * 0.6, 40)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=2)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, cnts, -1, 255, -1)  # preenche partes brancas da arte
    return filled


def _from_mask(mask):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask)
    min_area = mask.size * 0.0008
    out = []
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < min_area:
            continue

        # Trabalha só no bounding box do componente. A versão anterior fazia
        # (lab == i) sobre a imagem inteira para CADA componente, o que podia
        # transformar uma folha com muitos detalhes em trabalho O(n_componentes * pixels).
        x0, y0, w, h, _ = stats[i]
        comp = (lab[y0:y0 + h, x0:x0 + w] == i).astype(np.uint8)
        contours = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        cnt = max(contours, key=cv2.contourArea)
        cnt = cnt + np.array([x0, y0], dtype=cnt.dtype)
        (x, y), rm = cv2.minEnclosingCircle(cnt)
        area = cv2.contourArea(cnt)
        if area / (np.pi * rm * rm) > 0.85:  # botton isolado
            out.append((x, y, float(np.sqrt(area / np.pi))))
            continue
        dt = cv2.GaussianBlur(cv2.distanceTransform(comp, cv2.DIST_L2, 5), (0, 0), 2)
        peaks = (dt == cv2.dilate(dt, np.ones((15, 15)))) & (dt > 0.5 * dt.max())
        ys, xs = np.nonzero(peaks)
        cand = sorted(((float(x + x0), float(y + y0), float(dt[y, x])) for x, y in zip(xs, ys)), key=lambda c: -c[2])
        for c in cand:
            if all(np.hypot(c[0] - a, c[1] - b) > 0.9 * max(c[2], q) for a, b, q in out):
                out.append(c)
    return out


def _hough(small):
    g = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (9, 9), 2)
    m = min(small.shape[:2])
    f = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, 1.2, m * 0.12, param1=110, param2=45,
                         minRadius=int(m * 0.08), maxRadius=int(m * 0.35))
    return [] if f is None else [tuple(map(float, c)) for c in f[0]]


def _clean(cs):
    if not cs:
        return []
    big = max(c[2] for c in cs)  # o botton maior é a referência (letras/detalhes pequenos não mandam)
    cs = [c for c in cs if c[2] >= 0.4 * big]  # aceita bottons de tamanhos diferentes
    cs.sort(key=lambda c: -c[2])
    keep = []
    for c in cs:  # remove círculos dentro de outros / duplicados
        if all(np.hypot(c[0] - a, c[1] - b) > 0.9 * max(c[2], q) for a, b, q in keep):
            keep.append(c)
    return keep


def _fit(pts):
    """Círculo por mínimos quadrados (Kasa)."""
    x, y = pts[:, 0], pts[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    c, *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    return c[0], c[1], float(np.sqrt(max(c[2] + c[0] ** 2 + c[1] ** 2, 1e-6)))



def _outer_edge_fit(img, cx, cy, r, expected_r, n=360):
    """Localiza o contorno externo/aro do botton, mesmo quando a arte interna
    foi detectada com um raio menor. Usa bordas locais e uma amostra externa
    por direção, seguida de ajuste circular robusto."""
    h, w = img.shape[:2]
    base = max(float(r), float(expected_r) * 0.9)
    rmin = max(4.0, 0.82 * base)
    rmax = min(1.30 * float(expected_r), 1.42 * base)
    pad = int(rmax + 8)
    x0, y0 = max(0, int(cx - pad)), max(0, int(cy - pad))
    x1, y1 = min(w, int(cx + pad) + 1), min(h, int(cy + pad) + 1)
    roi = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    roi = cv2.GaussianBlur(roi, (5, 5), 1.0)
    edges = cv2.Canny(roi, 35, 100)
    yy, xx = np.nonzero(edges)
    if len(xx) < 80:
        return None
    xx = xx.astype(np.float32) + x0
    yy = yy.astype(np.float32) + y0
    rr = np.hypot(xx - cx, yy - cy)
    keep = (rr >= rmin) & (rr <= rmax)
    xx, yy, rr = xx[keep], yy[keep], rr[keep]
    if len(xx) < 80:
        return None
    ang = (np.arctan2(yy - cy, xx - cx) + 2 * np.pi) % (2 * np.pi)
    bins = np.floor(ang / (2 * np.pi) * n).astype(np.int32)
    pts = []
    for b in range(n):
        q = np.flatnonzero(bins == b)
        if q.size:
            j = q[np.argmax(rr[q])]
            pts.append((xx[j], yy[j]))
    if len(pts) < n * 0.35:
        return None
    pts = np.asarray(pts, dtype=np.float32)
    for _ in range(5):
        fx, fy, fr = _fit(pts)
        res = np.abs(np.hypot(pts[:, 0] - fx, pts[:, 1] - fy) - fr)
        med = np.median(res)
        keep = res <= max(2.5, 2.5 * med)
        if keep.sum() < n * 0.25:
            return None
        pts = pts[keep]
    fx, fy, fr = _fit(pts)
    if not (0.82 * expected_r <= fr <= 1.30 * expected_r):
        return None
    if np.hypot(fx - cx, fy - cy) > 0.25 * expected_r:
        return None
    return float(fx), float(fy), float(fr)

def _refine(img, cx, cy, r, n=240):
    """Ajusta o círculo à borda real do botton (maior gradiente de cor), ignorando a sombra."""
    h, w = img.shape[:2]
    sigma = max(1.0, r / 200)
    pad = int(4 * sigma) + 4   # folga p/ o borrão e a interpolação não "sentirem" a borda do recorte
    x0, y0 = max(0, int(cx - 1.12 * r) - pad), max(0, int(cy - 1.12 * r) - pad)
    x1, y1 = min(w, int(cx + 1.12 * r) + pad + 1), min(h, int(cy + 1.12 * r) + pad + 1)
    # borra só a região do círculo (em folha enorme, borrar a imagem inteira a cada botton levaria minutos)
    blur = cv2.GaussianBlur(np.ascontiguousarray(img[y0:y1, x0:x1]), (0, 0), sigma).astype(np.float32)
    rs = np.arange(0.8 * r, 1.12 * r, max(0.5, r / 300))
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    mx = (cx + rs[None] * np.cos(a)[:, None]).astype(np.float32)
    my = (cy + rs[None] * np.sin(a)[:, None]).astype(np.float32)
    m_ = len(rs)
    prof = cv2.remap(blur, mx - x0, my - y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mag = np.linalg.norm(np.gradient(prof, axis=1), axis=2)
    rowmax = mag.max(axis=1, keepdims=True)
    peak = (mag >= 0.5 * rowmax) & (mag >= np.roll(mag, 1, 1)) & (mag >= np.roll(mag, -1, 1))
    peak[:, 0] = peak[:, -1] = False
    peak[np.arange(n), mag.argmax(axis=1)] = True  # garante ao menos um pico
    idx = m_ - 1 - peak[:, ::-1].argmax(axis=1)  # pico mais EXTERNO (a sombra é fraca; a arte é interna)
    strong = mag.max(axis=1) > 0.35 * np.median(mag.max(axis=1))
    inside = (mx[np.arange(n), idx] > 0) & (mx[np.arange(n), idx] < w - 1) & \
             (my[np.arange(n), idx] > 0) & (my[np.arange(n), idx] < h - 1)
    ok = strong & inside
    if ok.sum() < n * 0.4:
        return cx, cy, r
    pts = np.c_[mx[np.arange(n), idx], my[np.arange(n), idx]][ok]
    for _ in range(4):  # remove pontos fora do círculo (outliers)
        fx, fy, fr = _fit(pts)
        res = np.abs(np.hypot(pts[:, 0] - fx, pts[:, 1] - fy) - fr)
        keep = res < max(2 * np.median(res), 0.01 * fr)
        if keep.sum() < 20:
            return cx, cy, r
        pts = pts[keep]
    fx, fy, fr = _fit(pts)
    if not (0.8 * r <= fr <= 1.12 * r) or np.hypot(fx - cx, fy - cy) > 0.15 * r:
        return cx, cy, r
    return fx, fy, fr * 0.99  # leve recuo p/ não pegar o aro/sombra


def detect_circles(img_bgr):
    """(cx, cy, r) na escala da imagem original, em ordem de leitura."""
    h, w = img_bgr.shape[:2]
    s = min(1.0, MAXSIDE / max(h, w))
    small = cv2.resize(img_bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img_bgr
    cs = _clean(_from_mask(_segment(small)))
    if not cs:
        cs = _clean(_hough(small))
    if not cs:
        return []
    row = np.median([c[2] for c in cs]) * 1.5
    cs.sort(key=lambda c: (round(c[1] / row), c[0]))
    # _refine já converte as coordenadas para a escala recebida. A versão
    # anterior chamava _refine duas vezes por botton, repetindo GaussianBlur,
    # remap, gradientes e ajuste por mínimos quadrados.
    expected_r = float(np.median([c[2] for c in cs]) / s)
    refined = []
    for x, y, r in cs:
        x, y, r = x / s, y / s, r / s
        outer = _outer_edge_fit(img_bgr, x, y, r, expected_r)
        if outer is not None:
            refined.append(outer)
        else:
            refined.append(_refine(img_bgr, x, y, r))
    return refined
