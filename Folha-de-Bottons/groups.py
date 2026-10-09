"""Identifica tipos (aparências) de bottons: bottons parecidos caem no mesmo grupo."""
import numpy as np
from PIL import ImageFilter
from process import art_circle

N = 32
_yy, _xx = np.mgrid[:N, :N]
MASK = np.hypot(_xx - N / 2 + .5, _yy - N / 2 + .5) < N / 2 * 0.85   # só o miolo da arte
TOL = 20.0   # diferença média (0-255) abaixo da qual dois bottons são "o mesmo"


def signature(src, cx, cy, r):
    """Miniatura suavizada da arte: não depende do tamanho do botton na imagem."""
    a = art_circle(src, cx, cy, r, 0, N).convert("RGB").filter(ImageFilter.GaussianBlur(1.0))
    return np.asarray(a, np.float32)


def distance(a, b):
    return float(np.abs(a - b)[MASK].mean())


def cluster(sigs, tol=TOL):
    """Rótulo de grupo (0, 1, 2...) para cada assinatura, na ordem de aparecimento."""
    reps, labels = [], []
    for s in sigs:
        d = [distance(s, r) for r in reps]
        if d and min(d) < tol:
            labels.append(int(np.argmin(d)))
        else:
            reps.append(s)
            labels.append(len(reps) - 1)
    return labels
