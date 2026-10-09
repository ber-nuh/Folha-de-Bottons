"""Aprende o 'molde' de iluminação a partir de um par COM/SEM iluminação (mesmo botton).
Uso: python build_template.py par.png  -> gera gloss_template.npz"""
import sys, cv2, numpy as np
from PIL import Image
from detect import detect_circles
from process import art_circle

def build(path, N=400, out="gloss_template.npz"):
    src = Image.open(path).convert("RGB")
    cs = sorted(detect_circles(cv2.cvtColor(np.asarray(src), cv2.COLOR_RGB2BGR)), key=lambda c: c[0])[:2]
    lit = np.asarray(art_circle(src, *cs[0], 0, N).convert("RGB"), np.float32) / 255
    gt = np.asarray(art_circle(src, *cs[1], 0, N).convert("RGB"), np.float32) / 255
    yy, xx = np.mgrid[:N, :N]
    m = (np.hypot(xx - N / 2 + .5, yy - N / 2 + .5) < N / 2 * 0.98).astype(np.float32)
    gl, gg = lit.mean(2), gt.mean(2)
    wm = np.eye(2, 3, dtype=np.float32)  # registra o sem-luz sobre o com-luz (afim)
    _, wm = cv2.findTransformECC(gl, gg, wm, cv2.MOTION_AFFINE,
                                 (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6),
                                 (m * 255).astype(np.uint8), 7)
    gt = cv2.warpAffine(gt, wm, (N, N), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    gg = gt.mean(2)
    B = lambda x, s=N * 0.12: cv2.GaussianBlur(x * m, (0, 0), s) / (cv2.GaussianBlur(m, (0, 0), s) + 1e-6)
    var = B(gg * gg) - B(gg) ** 2
    G = (B(gl * gg) - B(gl) * B(gg)) / (var + 0.01)          # ganho local (ridge)
    G = cv2.GaussianBlur(np.clip(G, 0.4, 1.6), (0, 0), N * 0.05)
    V = cv2.GaussianBlur(np.clip(B(gl) - G * B(gg), -0.3, 0.5), (0, 0), N * 0.05)
    rec = np.clip((lit - V[..., None]) / G[..., None], 0, 1)
    print("erro (interior 90%) original:", float(np.abs(lit - gt)[m > 0].mean() * 255),
          "| com molde:", float(np.abs(rec - gt)[m > 0].mean() * 255))
    np.savez(out, G=cv2.resize(G, (200, 200), interpolation=cv2.INTER_AREA).astype(np.float32),
             V=cv2.resize(V, (200, 200), interpolation=cv2.INTER_AREA).astype(np.float32))
    return lit, gt, rec, G, V

if __name__ == "__main__":
    build(sys.argv[1])
