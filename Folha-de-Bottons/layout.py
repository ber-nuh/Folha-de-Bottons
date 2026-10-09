"""Organização automática em grade e exportação PNG/PDF com DPI real."""
import math
from PIL import Image
from process import mm

SHEETS = {"A4": (210, 297), "A3": (297, 420)}
MARGIN = 5      # mm: margem padrão ("Centralizados" e início do "Canto superior esquerdo")
MARGIN_MIN = 3  # mm: menor folga por lado aceita no "Canto superior esquerdo" (cabe 3 bottons de 58 mm na A4)


def grid_size(total_mm, gap, W, H, align="center"):
    """(colunas, linhas) que cabem em uma página."""
    m = MARGIN if align == "center" else MARGIN_MIN
    cols = max(1, int((W - 2 * m + gap + 1e-6) // (total_mm + gap)))
    rows = max(1, int((H - 2 * m + gap + 1e-6) // (total_mm + gap)))
    return cols, rows


def positions(n, total_mm, gap, W, H, align="center"):
    """Canto superior esquerdo (mm) de cada botton, por página: [[(índice, x, y), ...], ...].
    align="center": bloco centralizado na folha, com margem de 5 mm.
    align="topleft": começa no canto superior esquerdo (margem de 5 mm). Para encaixar uma coluna/linha a mais,
    aceita folga de até 3 mm por lado; quando o bloco só cabe assim (ex.: 3 bottons de 58 mm na A4), ele
    fica centralizado na folha. 32 mm na A4 => 4 colunas; 58 mm na A4 => 3 colunas."""
    cols, rows = grid_size(total_mm, gap, W, H, align)
    per, pages = cols * rows, []
    for p in range(0, max(n, 1), per):
        cnt = max(0, min(per, n - p))
        nc = min(cols, cnt) or 1
        nr = math.ceil(cnt / cols)
        bw = cols * total_mm + (cols - 1) * gap   # largura da grade cheia (a mesma em todas as linhas)
        bh = nr * total_mm + (nr - 1) * gap
        if align == "topleft":
            x0 = min(MARGIN, max(0, (W - bw) / 2))
            y0 = min(MARGIN, max(0, (H - bh) / 2))
        else:
            x0 = (W - (nc * total_mm + (nc - 1) * gap)) / 2
            y0 = (H - bh) / 2
        pages.append([(p + i, x0 + (i % cols) * (total_mm + gap), y0 + (i // cols) * (total_mm + gap))
                      for i in range(cnt)])
    return pages


def build_pages(buttons, total_mm, gap, W, H, dpi, bg, align="center"):
    pages = []
    for pos in positions(len(buttons), total_mm, gap, W, H, align):
        page = Image.new("RGBA", (mm(W, dpi), mm(H, dpi)), bg)
        for i, x, y in pos:
            page.alpha_composite(buttons[i], (mm(x, dpi), mm(y, dpi)))
        pages.append(page)
    return pages


def export(pages, path, dpi, bg):
    if path.lower().endswith(".pdf"):
        flat = []
        for p in pages:  # PDF não tem alpha: compõe sobre o fundo (branco se transparente)
            base = Image.new("RGB", p.size, bg[:3] if bg[3] else (255, 255, 255))
            base.paste(p, mask=p.getchannel("A"))
            flat.append(base)
        flat[0].save(path, "PDF", resolution=dpi, save_all=True, append_images=flat[1:])
    else:
        stem = path.rsplit(".", 1)[0]
        for i, p in enumerate(pages):
            name = path if len(pages) == 1 else f"{stem}_{i + 1}.png"
            p.save(name, dpi=(dpi, dpi))
