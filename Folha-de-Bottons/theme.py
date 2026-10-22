"""Visual do programa: temas (cores + detalhes de estilo) trocáveis em tempo de execução.

Os temas foram refeitos para aproximar o programa de interfaces modernas, incluindo opções escuras, claras, Sálvia Mono, Editorial clássico, esmeralda e azul profundo
(as cores foram amostradas direto dos pixels das imagens):

  Tema padrão        o tema de fábrica (antigo \"Windows 11 escuro\"): grafite #202124 com destaque azul-claro #4CC2FF, janela 100% opaca
  Fluent escuro      app UWP/Fluent: grafite #2B2937, botões índigo #3D4979, destaque verde-água #1FB99D,
                     barra lateral azul (abas) e título com filete verde-água; fundo azul estilo Windows 11
  Claro minimalista  cronômetro: cinza #E8E8E8 + azul-petróleo #3D4961, detalhes pêssego #F4CFB5,
                     título em maiúsculas e a "linha do tempo" com a bolinha azul no topo
  Âmbar claro        "Focus Task": barra de título escura, painel branco, área de trabalho #F1F2F6, âmbar/laranja

  Windows 95         clássico: cinza #C0C0C0, barra de título azul-marinho #000080, botões/campos com chanfro 3D,
                     fonte MS Sans Serif, cantos retos e área de trabalho verde-azulada #008080

Cada tema é um dicionário de cores. Campos opcionais caem em valores derivados (ver set_theme).
"""
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import ctypes
import sys

import numpy as np
from PIL import Image

F = "Segoe UI"
S = 1.0  # fator de escala da interface (DPI do monitor / 96); definido em apply()

# HEADER_*   faixa do topo (HEADER_STYLE: "line" | "timeline" | "titlebar"; HEADER_LINE: filete inferior)
# PANEL      fundo dos painéis | CARD: campos e botões | TEXT/SEC/MUTED: textos | LINE: bordas
# ACC*       cor de destaque | ACTIVE: hover/seleção | BTN_BORDER: borda dos botões comuns
# TAB_*      abas (faixa, aba normal, aba selecionada)
# STAGE*     pré-visualização: fundo, degradê (4 cantos: sup-esq, sup-dir, inf-esq, inf-dir), textos e traço do estado vazio
# FONT       famílias de fonte em ordem de preferência | FONT_SIZE: tamanho base | CLASSIC: chanfros 3D (Windows 95)
# TITLEBAR   cor da barra de título (usada quando WINDOW_CAPTION="solid")
# WINDOW_*   moldura da janela (só Windows 11): EFFECT = "acrylic" (vidro) | "mica" | "mica_dark" | None;
#            CAPTION = "backdrop" (barra de título de vidro) | "solid" (barra na cor TITLEBAR);
#            BORDER = "none" (sem linha) | "default" (borda do Windows) | "soft-accent" (cor de destaque suave) | "#RRGGBB";
#            CORNER = 2 arredondado | 3 arredondado pequeno | 1 quadrado | 0 padrão do Windows;
#            ALPHA = EFEITO VIDRO DOS TEMAS: 1.0 opaco ... 0.9 bem translúcido (a janela inteira deixa ver o que está atrás).
#            Mexa aqui para ter mais ou menos vidro (abaixo de ~0.85 o texto começa a ficar difícil de ler).
#            EFFECT/CAPTION="backdrop" (Mica/Acrylic do Windows na barra de título) foram abandonados: não use junto com ALPHA.
# CD_PLAYER  True = nas Configurações, a área de música ganha o leitor estilo "CD Player" do Windows 95 (cdplayer.py)
# SHADOW     sombra da folha | NUM*: marcador "#" | PINS: cores dos pins decorativos do cabeçalho
THEMES = {
    "Tema padrão": dict(
        HEADER_BG="#202124", HEADER_FG="#FFFFFF", HEADER_SUB="#A9ACB2", HEADER_STYLE="line", HEADER_LINE="#4CC2FF",
        PANEL="#202124", CARD="#2B2D31", TEXT="#F5F7FA", SEC="#FFFFFF", MUTED="#A9ACB2", LINE="#3A3D43",
        BTN_BORDER="#444850", ACC="#4CC2FF", ACC_HOVER="#2AA8E6", ACC_FG="#07131A", ACTIVE="#353941",
        TAB_STRIP="#18191C", TAB_BG="#18191C", TAB_FG="#B9C0C8", TAB_SEL_BG="#30343A", TAB_SEL_FG="#FFFFFF",
        STAGE="#15171A", STAGE_GRAD=("#242A31", "#151A20", "#101216", "#0B0D10"), SHADOW="#08090B",
        STAGE_FG="#F5F7FA", STAGE_SUB="#A9ACB2", STAGE_LINE="#4CC2FF",
        NUM="#4CC2FF", NUM_FG="#07131A", PINS=("#4CC2FF", "#7B8CFF", "#D7E2EA"),
        WINDOW_EFFECT=None, WINDOW_BORDER="none", WINDOW_CORNER=2, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0, TITLEBAR="#202124", TITLE_FG="#FFFFFF"),

    "Claro moderno": dict(
        HEADER_BG="#F8FAFC", HEADER_FG="#172033", HEADER_SUB="#667085", HEADER_STYLE="timeline", HEADER_LINE="#D9E2EC",
        PANEL="#F8FAFC", CARD="#FFFFFF", TEXT="#172033", SEC="#25324A", MUTED="#667085", LINE="#D9E2EC",
        BTN_BORDER="#D0D8E2", ACC="#2563EB", ACC_HOVER="#1D4ED8", ACC_FG="#FFFFFF", ACTIVE="#E8F0FE",
        TAB_STRIP="#1E293B", TAB_BG="#1E293B", TAB_FG="#B8C2D1", TAB_SEL_BG="#FFFFFF", TAB_SEL_FG="#2563EB",
        STAGE="#EEF2F7", SHADOW="#CBD5E1",
        STAGE_FG="#172033", STAGE_SUB="#667085", STAGE_LINE="#2563EB",
        NUM="#2563EB", NUM_FG="#FFFFFF", PINS=("#2563EB", "#93C5FD", "#CBD5E1"),
        WINDOW_EFFECT=None, WINDOW_BORDER="#E6EBF2", WINDOW_CORNER=2, WINDOW_CAPTION="solid", WINDOW_ALPHA=0.96, TITLEBAR="#F8FAFC", TITLE_FG="#172033"),

    "Sálvia Mono": dict(
        HEADER_BG="#EAF0E5", HEADER_FG="#26352D", HEADER_SUB="#64756A", HEADER_STYLE="line", HEADER_LINE="#9AAE91",
        PANEL="#EAF0E5", CARD="#F7F9F4", TEXT="#26352D", SEC="#34463A", MUTED="#64756A", LINE="#C8D2C2",
        BTN_BORDER="#B8C5B2", ACC="#9AAE91", ACC_HOVER="#829A78", ACC_FG="#17251B", ACTIVE="#DCE6D6",
        TAB_STRIP="#DCE5D7", TAB_BG="#DCE5D7", TAB_FG="#536457", TAB_SEL_BG="#F7F9F4", TAB_SEL_FG="#34463A",
        STAGE="#E0E8DA", SHADOW="#C3CEBD",
        STAGE_FG="#26352D", STAGE_SUB="#64756A", STAGE_LINE="#819A78",
        NUM="#819A78", NUM_FG="#FFFFFF", PINS=("#819A78", "#B5C6A9", "#E9EFE4"),
        WINDOW_EFFECT=None, WINDOW_BORDER="#C8D2C2", WINDOW_CORNER=2, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0,
        TITLEBAR="#EAF0E5", TITLE_FG="#26352D"),

    "Editorial clássico": dict(
        HEADER_BG="#E8E1D0", HEADER_FG="#30291F", HEADER_SUB="#756A58", HEADER_STYLE="line", HEADER_LINE="#8B7355",
        PANEL="#E8E1D0", CARD="#F4EEDF", TEXT="#30291F", SEC="#3C3328", MUTED="#756A58", LINE="#C8BDA7",
        BTN_BORDER="#B8AA91", ACC="#8B7355", ACC_HOVER="#725B40", ACC_FG="#FFFDF7", ACTIVE="#DCD0B8",
        TAB_STRIP="#D8CEB8", TAB_BG="#D8CEB8", TAB_FG="#5E5140", TAB_SEL_BG="#F4EEDF", TAB_SEL_FG="#30291F",
        STAGE="#D8CEB8", SHADOW="#BBAE96",
        STAGE_FG="#30291F", STAGE_SUB="#756A58", STAGE_LINE="#8B7355",
        NUM="#8B7355", NUM_FG="#FFFDF7", PINS=("#8B7355", "#B6A486", "#EDE4D2"),
        FONT=("Georgia", "Times New Roman", "DejaVu Serif"), FONT_SIZE=10,
        WINDOW_EFFECT=None, WINDOW_BORDER="#B8AA91", WINDOW_CORNER=1, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0,
        TITLEBAR="#E8E1D0", TITLE_FG="#30291F"),

    "Verde esmeralda": dict(
        HEADER_BG="#10201B", HEADER_FG="#FFFFFF", HEADER_SUB="#94A9A1", HEADER_STYLE="line", HEADER_LINE="#22C55E",
        PANEL="#10201B", CARD="#193029", TEXT="#EFFAF4", SEC="#FFFFFF", MUTED="#94A9A1", LINE="#2A453C",
        BTN_BORDER="#315449", ACC="#22C55E", ACC_HOVER="#16A34A", ACC_FG="#06140B", ACTIVE="#244238",
        TAB_STRIP="#0A1612", TAB_BG="#0A1612", TAB_FG="#A7BDB3", TAB_SEL_BG="#214238", TAB_SEL_FG="#FFFFFF",
        STAGE="#0C1713", STAGE_GRAD=("#173D31", "#102B22", "#0B1712", "#07100D"), SHADOW="#050B08",
        STAGE_FG="#F1FFF6", STAGE_SUB="#A9C3B7", STAGE_LINE="#22C55E",
        NUM="#22C55E", NUM_FG="#06140B", PINS=("#22C55E", "#60A5FA", "#D1FAE5"),
        WINDOW_EFFECT=None, WINDOW_BORDER="none", WINDOW_CORNER=2, WINDOW_CAPTION="solid", WINDOW_ALPHA=0.90, TITLEBAR="#10201B", TITLE_FG="#FFFFFF"),

    "Azul profundo transparente": dict(
        HEADER_BG="#0B1B33", HEADER_FG="#F5FAFF", HEADER_SUB="#AFC7E6", HEADER_STYLE="line", HEADER_LINE="#2D8CFF",
        PANEL="#0B1B33", CARD="#102744", TEXT="#F4F8FF", SEC="#FFFFFF", MUTED="#9FB6D3", LINE="#24415F",
        BTN_BORDER="#315579", ACC="#3D9BFF", ACC_HOVER="#68B3FF", ACC_FG="#061426", ACTIVE="#183B61",
        TAB_STRIP="#071326", TAB_BG="#0B1B33", TAB_FG="#AFC7E6", TAB_SEL_BG="#164A78", TAB_SEL_FG="#FFFFFF",
        STAGE="#081A31", STAGE_GRAD=("#173E67", "#0D2948", "#08182C", "#050E1A"), SHADOW="#030A12",
        STAGE_FG="#F5FAFF", STAGE_SUB="#AFC7E6", STAGE_LINE="#3D9BFF",
        NUM="#3D9BFF", NUM_FG="#061426", PINS=("#3D9BFF", "#69C0FF", "#DCEEFF"),
        WINDOW_EFFECT=None, WINDOW_BORDER="none", WINDOW_CORNER=2, WINDOW_CAPTION="solid", WINDOW_ALPHA=0.90, TITLEBAR="#0B1B33", TITLE_FG="#F5FAFF"),

    "Windows 95 clássico": dict(
        HEADER_BG="#C0C0C0", HEADER_FG="#000000", HEADER_SUB="#404040", HEADER_STYLE="win95",
        PANEL="#C0C0C0", CARD="#FFFFFF", TEXT="#000000", SEC="#000000", MUTED="#808080", LINE="#808080",
        BTN_BORDER="#404040", ACC="#000080", ACC_HOVER="#000080", ACC_FG="#FFFFFF", ACTIVE="#C0C0C0",
        TAB_STRIP="#C0C0C0", TAB_BG="#C0C0C0", TAB_FG="#000000", TAB_SEL_BG="#C0C0C0", TAB_SEL_FG="#000000",
        STAGE="#008080", SHADOW="#004848",
        STAGE_FG="#FFFFFF", STAGE_SUB="#FFFFFF", STAGE_LINE="#FFFFFF",
        NUM="#000080", NUM_FG="#FFFFFF", PINS=("#000080", "#808080", "#FFFFFF"),
        FONT=("MS Sans Serif", "Microsoft Sans Serif", "Tahoma", "Arial"), FONT_SIZE=8, CLASSIC=True,
        TITLEBAR="#000080", TITLE_FG="#FFFFFF", CD_PLAYER=True,
        WINDOW_BORDER="default", WINDOW_CORNER=1, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0)
}

DEFAULT = "Tema padrão"   # tema de fábrica: é o que vale na primeira vez que o programa abre (sem config salva)
NAME = DEFAULT
RENAMED = {"Windows 11 escuro": "Tema padrão"}   # nomes antigos que ainda podem estar no config salvo

# valores usados quando o tema não define o campo
_OPTIONAL = dict(HEADER_STYLE="line", HEADER_LINE=None, STAGE_GRAD=None, WINDOW_EFFECT=None,
                 WINDOW_BORDER="default", WINDOW_CORNER=0, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0,
                 FONT=("Segoe UI",), FONT_SIZE=10, CLASSIC=False, TITLEBAR=None, TITLE_FG="#FFFFFF",
                 CD_PLAYER=False)
CAPTION_SET = False
FRAME_SET = False   # já pintamos a barra de título do Windows (para desfazer ao trocar de tema)
_DERIVED = (("TAB_STRIP", "PANEL"), ("TAB_BG", "ACTIVE"), ("TAB_FG", "MUTED"), ("TAB_SEL_BG", "CARD"),
            ("TAB_SEL_FG", "ACC"), ("STAGE_FG", "TEXT"), ("STAGE_SUB", "MUTED"), ("STAGE_LINE", "MUTED"),
            ("BTN_BORDER", "LINE"), ("DISABLED", "MUTED"))


# ---------- acessibilidade: tamanho do texto e alto contraste ----------
TEXT_SIZES = {"Normal (100%)": 1.0, "Grande (125%)": 1.25, "Muito grande (150%)": 1.5, "Gigante (175%)": 1.75}
TEXT_SCALE = 1.0    # fator aplicado a TODAS as letras do programa
CONTRAST = False    # True = paleta de alto contraste calculada a partir do tema escolhido


def set_text_scale(v):
    """Aceita o fator (1.0, 1.25...) ou o rótulo de TEXT_SIZES; valor inválido volta para 100%."""
    global TEXT_SCALE
    v = TEXT_SIZES.get(v, v)
    TEXT_SCALE = float(v) if v in TEXT_SIZES.values() else 1.0


def set_contrast(on):
    """Liga/desliga o alto contraste e recalcula as cores do tema atual. Depois chame apply()."""
    global CONTRAST
    CONTRAST = bool(on)
    set_theme(NAME)


def fsize(cap=None):
    """Tamanho base da letra (pt) já com o fator de texto. cap = fator máximo (para peças de tamanho fixo)."""
    sc = TEXT_SCALE if cap is None else min(TEXT_SCALE, cap)
    return max(6, int(round(FONT_SIZE * sc)))


def fz(n, cap=None):
    """Como fsize, para um tamanho qualquer (títulos, textos desenhados no canvas...)."""
    sc = TEXT_SCALE if cap is None else min(TEXT_SCALE, cap)
    return max(6, int(round(n * sc)))


def wrap(v):
    """Largura (px) de quebra de linha para textos criados agora: acompanha o tamanho do texto."""
    return px(v * TEXT_SCALE)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in c)


def _lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _cr(a, b):
    """Taxa de contraste WCAG entre duas cores (1 a 21)."""
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ra[i] * (1 - t) + rb[i] * t for i in range(3)))


def _best(bg):
    """Branco ou preto, o que contrasta mais com 'bg'."""
    return "#FFFFFF" if _cr("#FFFFFF", bg) >= _cr("#000000", bg) else "#000000"


def _ensure(bg, fg, ratio):
    """Escurece/clareia 'bg' (afastando de 'fg', que é branco ou preto) até o contraste chegar a 'ratio'."""
    away = "#000000" if fg == "#FFFFFF" else "#FFFFFF"
    for _ in range(25):
        if _cr(bg, fg) >= ratio:
            break
        bg = _mix(bg, away, 0.07)
    return bg


def _high_contrast(d):
    """Versão de alto contraste (mínimo 7:1 nos textos) de qualquer tema: mantém o fundo e a cor de destaque
    de cada tema, mas põe letras puras, bordas marcadas e tira o efeito de vidro (translúcido)."""
    d = dict(d)
    dark = _lum(d["PANEL"]) < 0.4
    ink = "#FFFFFF" if dark else "#000000"
    line = "#B8B8B8" if dark else "#3A3A3A"
    d.update(TEXT=ink, SEC=ink, MUTED="#E4E4E4" if dark else "#1F1F1F", LINE=line, BTN_BORDER=line,
             DISABLED="#8C8C8C" if dark else "#6A6A6A", WINDOW_EFFECT=None, WINDOW_BORDER="default", WINDOW_CORNER=0, WINDOW_CAPTION="solid", WINDOW_ALPHA=1.0)
    d["TAB_FG"] = _best(d["TAB_BG"])
    d["TAB_SEL_FG"] = _best(d["TAB_SEL_BG"])
    d["HEADER_FG"] = _best(d["HEADER_BG"])
    d["HEADER_SUB"] = _mix(d["HEADER_FG"], d["HEADER_BG"], .1)
    fg = _best(d["ACC"])
    d["ACC"], d["ACC_FG"] = _ensure(d["ACC"], fg, 7), fg
    d["ACC_HOVER"] = _ensure(d["ACC_HOVER"], fg, 7)
    sfg = _best(d["STAGE"])
    if not d.get("STAGE_GRAD"):
        d["STAGE"] = _ensure(d["STAGE"], sfg, 7)
    d["STAGE_FG"], d["STAGE_SUB"], d["STAGE_LINE"] = sfg, sfg, sfg   # subtítulo também em cor pura: garante 7:1
    nfg = _best(d["NUM"])
    d["NUM"], d["NUM_FG"] = _ensure(d["NUM"], nfg, 7), nfg
    return d


def set_theme(name):
    """Troca as cores (variáveis do módulo). Depois chame apply() e recolora os widgets."""
    global NAME
    name = RENAMED.get(name, name)
    NAME = name if name in THEMES else DEFAULT   # sem config (primeira abertura) ou nome desconhecido: tema padrão
    d = dict(_OPTIONAL)
    d.update(THEMES[NAME])
    for k, ref in _DERIVED:
        d.setdefault(k, d[ref])
    if CONTRAST:
        d = _high_contrast(d)
    globals().update(d)


set_theme(DEFAULT)


def px(v):
    """Converte pixels 'de projeto' (96 dpi) para pixels reais da tela."""
    return max(1, int(round(v * S)))


def _bgr(hexcolor):
    h = hexcolor.lstrip("#")
    return (int(h[4:6], 16) << 16) | (int(h[2:4], 16) << 8) | int(h[0:2], 16)   # COLORREF = 0x00BBGGRR


_DWMS_READY = False
_DWM_AUTO, _DWM_NONE = 0xFFFFFFFF, 0xFFFFFFFE   # DWMWA_COLOR_DEFAULT / DWMWA_COLOR_NONE


class _MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]


def _prepare_dwm():
    """Configura assinaturas das APIs do DWM para funcionar corretamente em Windows 64-bit."""
    global _DWMS_READY
    if _DWMS_READY or sys.platform != "win32":
        return
    try:
        d = ctypes.windll.dwmapi
        d.DwmSetWindowAttribute.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
        d.DwmSetWindowAttribute.restype = ctypes.c_long
        d.DwmExtendFrameIntoClientArea.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        d.DwmExtendFrameIntoClientArea.restype = ctypes.c_long
        u = ctypes.windll.user32
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        u.GetAncestor.restype = ctypes.c_void_p
        _DWMS_READY = True
    except Exception:
        _DWMS_READY = False


def _dwm(hwnd, attr, value, ctype=ctypes.c_uint):
    _prepare_dwm()
    v = ctype(value)
    return ctypes.windll.dwmapi.DwmSetWindowAttribute(
        ctypes.c_void_p(hwnd), int(attr), ctypes.byref(v), ctypes.sizeof(v))


def _no_glass_in_content(hwnd):
    """Zera a extensão do vidro para dentro da janela.
    NUNCA estender o vidro por cima do conteúdo: o Tkinter desenha com GDI, e GDI sobre vidro fica transparente.
    O resultado é a janela inteira em branco (só o vidro aparece e o conteúdo some)."""
    _prepare_dwm()
    m = _MARGINS(0, 0, 0, 0)
    return ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(ctypes.c_void_p(hwnd), ctypes.byref(m))


def _window_hwnd(root):
    """HWND da janela de cima, a que tem a barra de título e a borda.
    winfo_id() do Tk devolve só a área interna; GetAncestor(GA_ROOT) sobe até a janela de verdade
    (e devolve a própria janela se ela já for a de cima). Antes de a janela aparecer pela primeira vez
    essa janela ainda não existe: por isso apply() repete o ajuste logo depois que ela aparece."""
    try:
        child = int(root.winfo_id())
    except Exception:
        return 0
    try:
        _prepare_dwm()
        top = ctypes.windll.user32.GetAncestor(ctypes.c_void_p(child), 2)   # GA_ROOT
        return int(top) if top else child
    except Exception:
        return child


def _border_value(border):
    """Valor de DWMWA_BORDER_COLOR para WINDOW_BORDER. O Windows não aceita transparência real na borda:
    'none' tira a linha (a janela fica só com a sombra) e 'soft-accent' mistura a cor de destaque com o
    fundo do tema, o que dá o aspecto de borda translúcida."""
    if border == "none":
        return _DWM_NONE
    if border in ("default", None):
        return _DWM_AUTO
    if border == "soft-accent":
        return _bgr(_mix(ACC, PANEL, 0.45))
    return _bgr(border)


def _glass():
    """True quando a barra de título deve ser de vidro (Acrylic/Mica)."""
    return bool(WINDOW_EFFECT) and WINDOW_CAPTION == "backdrop"


def _apply_caption(root):
    """Aplica a moldura DWM do tema atual (Windows 11; no Windows 10 o que não existir é ignorado).

    Temas modernos: cantos arredondados, borda discreta e barra de título de vidro (Acrylic/Mica) ou na cor
    do tema. A sombra externa é a do próprio Windows. O Windows 95 volta à moldura clássica: opaca,
    quadrada, com a barra azul-marinho."""
    global CAPTION_SET, FRAME_SET
    if sys.platform != "win32":
        return
    try:
        hwnd = _window_hwnd(root)
        if not hwnd:
            return
        _no_glass_in_content(hwnd)                                    # conteúdo sempre opaco e visível
        _dwm(hwnd, 33, int(WINDOW_CORNER), ctypes.c_int)              # cantos
        _dwm(hwnd, 34, _border_value(WINDOW_BORDER), ctypes.c_uint)   # borda
        FRAME_SET = True
        if _glass():
            _dwm(hwnd, 35, _DWM_NONE, ctypes.c_uint)   # sem cor sólida: a barra mostra o vidro
            text = TITLE_FG or HEADER_FG
            dark = WINDOW_EFFECT in ("mica_dark", "acrylic")
        else:
            caption = TITLEBAR or HEADER_BG
            text = TITLE_FG if TITLEBAR else HEADER_FG
            _dwm(hwnd, 35, _bgr(caption), ctypes.c_uint)
            dark = _lum(caption) < 0.4           # barra escura => botões (— ▢ ✕) claros
        _dwm(hwnd, 36, _bgr(text), ctypes.c_uint)
        for attr in (20, 19):                    # 20 = Windows 11/10 recente; 19 = Windows 10 antigo
            _dwm(hwnd, attr, 1 if dark else 0, ctypes.c_int)
        CAPTION_SET = True
    except Exception:
        pass


def _apply_windows_effect(root):
    """Aplica a moldura do tema atual: translucidez, barra de título e vidro (Mica/Acrylic)."""
    if sys.platform != "win32":
        return
    glass = _glass()   # só True se algum tema pedir barra de título "backdrop" (nenhum pede mais)
    try:
        # O efeito vidro dos temas é a translucidez da janela inteira (-alpha = WINDOW_ALPHA do tema).
        # O Mica/Acrylic do Windows NÃO é usado junto: com os dois a janela fica branca. O -alpha vem ANTES
        # do resto porque mudar o estilo da janela pode fazer o Tk recriar a janela, e aí os ajustes
        # anteriores se perderiam.
        root.attributes("-alpha", 1.0 if glass else max(0.6, min(1.0, float(WINDOW_ALPHA))))
        root.update_idletasks()
    except Exception:
        pass
    _apply_caption(root)
    try:
        hwnd = _window_hwnd(root)
        if hwnd:
            # DWMWA_SYSTEMBACKDROP_TYPE = 38: 1=nenhum, 2=Mica, 3=Acrylic.
            _dwm(hwnd, 38, (3 if WINDOW_EFFECT == "acrylic" else 2) if glass else 1, ctypes.c_int)
    except Exception:
        pass


def _apply_effect_soon(root, tries=0):
    """Repete o ajuste da moldura logo depois que a janela aparece. Na abertura do programa a janela do
    Windows ainda não existe quando apply() roda, e sem isto a barra de título ficava no padrão do Windows."""
    old = getattr(root, "_effect_job", None)
    if old:
        try:
            root.after_cancel(old)
        except Exception:
            pass

    def run():
        root._effect_job = None
        try:
            mapped = bool(root.winfo_ismapped())
        except Exception:
            return   # janela já fechada
        if mapped:
            _apply_windows_effect(root)
        elif tries < 40:
            _apply_effect_soon(root, tries + 1)

    try:
        root._effect_job = root.after(120, run)
    except Exception:
        pass


def apply(root):
    """Aplica o tema atual aos widgets ttk. Visual reto (sem imagens de cantos arredondados): leve e rápido."""
    global S, F
    S = min(3.0, max(1.0, root.winfo_fpixels("1i") / 96))   # monitores de alta densidade (4K, 125%, 150%...)
    fams = set(tkfont.families(root))
    F = next((f for f in FONT if f in fams), FONT[-1])   # MS Sans Serif no Windows 95; Segoe UI nos demais
    fs = fsize()
    root.configure(bg=PANEL)
    _apply_windows_effect(root)
    _apply_effect_soon(root)   # repete quando a janela já estiver na tela
    root.option_add("*TCombobox*Listbox.background", CARD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACC)
    root.option_add("*TCombobox*Listbox.selectForeground", ACC_FG)
    root.option_add("*TCombobox*Listbox.font", (F, fs))
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure(".", background=PANEL, foreground=TEXT, font=(F, fs), bordercolor=LINE, focuscolor=PANEL,
                 lightcolor=LINE, darkcolor=LINE, troughcolor=LINE)
    st.map(".", foreground=[("disabled", DISABLED)])
    st.configure("TFrame", background=PANEL)
    st.configure("TLabel", background=PANEL, foreground=TEXT)
    st.configure("Sec.TLabel", font=(F, fs, "bold"), foreground=SEC)
    st.configure("Info.TLabel", foreground=MUTED, font=(F, fs if (CLASSIC or CONTRAST) else fs - 1))
    # botões: no hover ganham a cor de seleção do tema e a borda de destaque
    st.configure("TButton", background=CARD, foreground=TEXT, padding=(10, 6), relief="flat", borderwidth=1,
                 bordercolor=BTN_BORDER, lightcolor=CARD, darkcolor=CARD)
    st.map("TButton", background=[("active", ACTIVE)], bordercolor=[("active", ACC)],
           lightcolor=[("active", ACTIVE)], darkcolor=[("active", ACTIVE)], foreground=[("disabled", DISABLED)])
    st.configure("Mini.TButton", padding=(2, 4))
    # Botão de próxima página em alerta: usado pelo app para indicar que existem
    # bottons em páginas seguintes. O app alterna entre este estilo e Mini.TButton.
    st.configure("NextAlert.TButton", background=ACC, foreground=ACC_FG, padding=(2, 4),
                 relief="flat", borderwidth=1, bordercolor=ACC, lightcolor=ACC, darkcolor=ACC)
    st.map("NextAlert.TButton", background=[("active", ACC_HOVER)],
           foreground=[("active", ACC_FG), ("disabled", DISABLED)],
           bordercolor=[("active", ACC_HOVER)], lightcolor=[("active", ACC_HOVER)],
           darkcolor=[("active", ACC_HOVER)])
    st.configure("Accent.TButton", background=ACC, foreground=ACC_FG, font=(F, fs, "bold"),
                 padding=(10, 9), borderwidth=0, bordercolor=ACC, lightcolor=ACC, darkcolor=ACC)
    st.map("Accent.TButton", background=[("active", ACC_HOVER)], foreground=[("disabled", DISABLED), ("active", ACC_FG)],
           bordercolor=[("active", ACC_HOVER)], lightcolor=[("active", ACC_HOVER)], darkcolor=[("active", ACC_HOVER)])
    ind = int(round(10 * TEXT_SCALE))   # caixinha/bolinha cresce com o texto (10 px = padrão do tema "clam", ou seja, igual a antes em 100%)
    for w in ("TRadiobutton", "TCheckbutton"):
        st.configure(w, background=PANEL, foreground=TEXT, indicatorbackground=CARD, indicatorcolor=CARD,
                     indicatorforeground=ACC, indicatorsize=ind)   # marca (✓ / •) na cor de destaque: visível em temas claros e escuros
        st.map(w, indicatorcolor=[("selected", ACC)], background=[("active", PANEL)],
               foreground=[("disabled", DISABLED)])
    # abas = "barra lateral" do tema
    tab_pad = (px(16), px(8))
    st.configure("TNotebook", background=TAB_STRIP, borderwidth=0, tabmargins=(0, 0, 0, 0))
    st.configure("TNotebook.Tab", background=TAB_BG, foreground=TAB_FG, padding=tab_pad,
                 font=(F, fs, "bold"), borderwidth=0, bordercolor=TAB_BG, lightcolor=TAB_BG, darkcolor=TAB_BG)
    # padding/expand: o tema "clam" muda o tamanho da aba selecionada; aqui ela fica do mesmo tamanho das outras
    st.map("TNotebook.Tab", background=[("selected", TAB_SEL_BG)], foreground=[("selected", TAB_SEL_FG)],
           bordercolor=[("selected", TAB_SEL_BG)], lightcolor=[("selected", TAB_SEL_BG)],
           darkcolor=[("selected", TAB_SEL_BG)], padding=[("selected", tab_pad)],
           expand=[("selected", (0, 0, 0, 0))])
    st.configure("TSpinbox", fieldbackground=CARD, foreground=TEXT, padding=4, arrowcolor=TEXT, insertcolor=TEXT)
    st.configure("TScale", background=CARD, troughcolor=LINE)
    st.configure("TEntry", fieldbackground=CARD, foreground=TEXT, padding=5, insertcolor=TEXT)
    st.configure("TCombobox", fieldbackground=CARD, foreground=TEXT, padding=4, arrowcolor=TEXT, background=CARD)
    st.map("TCombobox", fieldbackground=[("readonly", CARD)], foreground=[("readonly", TEXT)],
           selectbackground=[("readonly", CARD)], selectforeground=[("readonly", TEXT)])
    for w in ("TEntry", "TSpinbox", "TCombobox"):   # anel de foco na cor de destaque
        st.map(w, bordercolor=[("focus", ACC)], lightcolor=[("focus", ACC)], darkcolor=[("focus", ACC)])
    st.configure("Vertical.TScrollbar", background=LINE, troughcolor=PANEL, bordercolor=PANEL, arrowcolor=MUTED,
                 lightcolor=LINE, darkcolor=LINE)
    st.map("Vertical.TScrollbar", background=[("active", MUTED)])
    if CLASSIC:
        _classic_styles(st, fs)


def _classic_styles(st, fs):
    """Windows 95: chanfro 3D cinza (branco em cima/esquerda, cinza escuro embaixo/direita), sem hover, sem cantos."""
    HI, SH, DK = "#FFFFFF", "#808080", "#404040"
    for name, bold in (("TButton", False), ("Accent.TButton", True)):
        st.configure(name, background=PANEL, foreground=TEXT, relief="raised", borderwidth=2,
                     padding=(px(10), px(5 if bold else 3)), font=(F, fs, "bold") if bold else (F, fs),
                     bordercolor="#000000" if bold else DK, lightcolor=HI, darkcolor=SH)   # destacado = contorno preto
        st.map(name, background=[("active", PANEL), ("pressed", PANEL)], foreground=[("disabled", SH), ("active", TEXT)],
               bordercolor=[], lightcolor=[("pressed", SH)], darkcolor=[("pressed", HI)], relief=[("pressed", "sunken")])
    for w in ("TRadiobutton", "TCheckbutton"):   # caixinha branca com marca preta
        st.configure(w, background=PANEL, foreground=TEXT, indicatorbackground=HI, indicatorcolor=HI,
                     indicatorforeground="#000000", bordercolor=SH, lightcolor=HI, darkcolor=DK)
        st.map(w, indicatorcolor=[("disabled", PANEL)], background=[("active", PANEL)], foreground=[("disabled", SH)])
    st.configure("TNotebook", background=PANEL, borderwidth=2, tabmargins=(px(2), px(2), 0, 0),
                 bordercolor=DK, lightcolor=HI, darkcolor=SH)
    st.configure("TNotebook.Tab", background=PANEL, foreground="#000000", padding=(px(10), px(3)), font=(F, fs),
                 borderwidth=1, bordercolor=DK, lightcolor=HI, darkcolor=SH)
    st.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", "#000000")],
           bordercolor=[("selected", DK)], lightcolor=[("selected", HI)], darkcolor=[("selected", SH)],
           padding=[("selected", (px(10), px(5)))], expand=[("selected", (px(2), px(2), px(2), 0))])
    for w in ("TEntry", "TSpinbox", "TCombobox"):   # campos "afundados"; as setas ficam em relevo
        st.configure(w, fieldbackground=HI, background=PANEL, foreground="#000000", padding=px(3), arrowcolor="#000000",
                     insertcolor="#000000", bordercolor=SH, lightcolor=HI, darkcolor=DK)
        st.map(w, bordercolor=[], lightcolor=[], darkcolor=[])
    st.map("TCombobox", fieldbackground=[("readonly", HI)], foreground=[("readonly", "#000000")],
           selectbackground=[("readonly", HI)], selectforeground=[("readonly", "#000000")])
    st.configure("Vertical.TScrollbar", background=PANEL, troughcolor="#E0E0E0", bordercolor=DK, arrowcolor="#000000",
                 lightcolor=HI, darkcolor=SH, arrowsize=px(16), gripcount=0, relief="raised", borderwidth=2)
    st.map("Vertical.TScrollbar", background=[("active", PANEL)])
    st.configure("TScale", background=PANEL, troughcolor=SH, bordercolor=SH, lightcolor=HI, darkcolor=SH)
    st.configure("TSeparator", background=SH)


# ---------- cabeçalho ----------
def _rrect(c, x0, y0, x1, y1, r, **kw):
    """Retângulo de cantos arredondados."""
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


def _pins(c, w, h):
    """Os três pins decorativos do canto direito."""
    for dx, r, col in ((150, 12, PINS[2]), (110, 17, PINS[1]), (56, 23, PINS[0])):
        cx, r = w - px(dx), px(r)
        c.create_oval(cx - r, h // 2 - r, cx + r, h // 2 + r, fill=col, outline="#FFFFFF", width=px(3))
        c.create_arc(cx - r * .6, h // 2 - r * .6, cx + r * .6, h // 2 + r * .6, start=100, extent=70,
                     style="arc", outline="#FFFFFF", width=px(2))  # brilho do pin


def _timeline(c, w, h):
    """Detalhe do tema minimalista: linha fina com duas barras pêssego e a bolinha azul (como no cronômetro)."""
    bar, line, dot = PINS
    cy, r = h // 2, px(17)
    c.create_line(w - px(340), cy, w - px(40) - r - px(10), cy, fill=line, width=px(1))
    for a, b in ((300, 246), (206, 112)):
        c.create_rectangle(w - px(a), cy - px(4), w - px(b), cy + px(4), fill=bar, outline="")
    c.create_oval(w - px(40) - r, cy - r, w - px(40) + r, cy + r, fill=dot, outline="")


def _win95_header(c, w, h, title, sub):
    """Cabeçalho do Windows 95: cinza, título em negrito, linha 'esculpida' (escura + branca) embaixo.
    (A barra de título azul-marinho é a do próprio Windows, pintada por _apply_caption.)"""
    t = max(1, px(1))
    c.create_text(px(12), h // 2 - int(h * .156), anchor="w", text=title, fill=HEADER_FG,
                  font=(F, fz(FONT_SIZE + 4, 1.5), "bold"))
    c.create_text(px(13), h // 2 + int(h * .1875), anchor="w", text=sub, fill=HEADER_SUB, font=(F, fz(FONT_SIZE, 1.5)))
    c.create_rectangle(0, h - 2 * t, w, h - t, fill="#808080", outline="")
    c.create_rectangle(0, h - t, w, h, fill="#FFFFFF", outline="")


def header(root, title, sub, h=64):
    c = tk.Canvas(root, height=px(h), highlightthickness=0, bd=0, bg=HEADER_BG)

    def draw(_=None):
        hh = px(h * min(TEXT_SCALE, 1.5))   # a faixa cresce junto com o texto (até 150%)
        if int(float(c.cget("height"))) != hh:
            c.configure(height=hh)
        c.delete("all")
        w = max(c.winfo_width(), 2)
        if HEADER_STYLE == "win95":
            _win95_header(c, w, hh, title, sub)
            return
        st, x0, ty, sy, tfont = HEADER_STYLE, px(24), int(hh * .375), int(hh * .734), (F, fz(17, 1.5), "bold")
        title_ = title
        if st == "titlebar":      # ícone do app (quadrado âmbar com ✓) + título, como a barra do Focus Task
            sz = px(34)
            lx, ly = px(22), (hh - sz) // 2
            _rrect(c, lx, ly, lx + sz, ly + sz, px(9), fill=ACC, outline="")
            c.create_line(lx + .26 * sz, ly + .52 * sz, lx + .43 * sz, ly + .69 * sz, lx + .75 * sz, ly + .33 * sz,
                          fill="#FFFFFF", width=px(3), capstyle="round", joinstyle="round")
            x0, ty, sy = lx + sz + px(14), hh // 2 - int(hh * .14), hh // 2 + int(hh * .22)
        elif st == "timeline":    # chevron + título em maiúsculas
            c.create_line(px(24), ty - px(3), px(29), ty + px(2), px(34), ty - px(3),
                          fill=HEADER_FG, width=px(2), capstyle="round", joinstyle="round")
            x0, title_, tfont = px(46), title.upper(), (F, fz(15, 1.5), "bold")
        c.create_text(x0, ty, anchor="w", text=title_, fill=HEADER_FG, font=tfont)
        c.create_text(x0 + px(1), sy, anchor="w", text=sub, fill=HEADER_SUB, font=(F, fz(9, 1.5)))
        if HEADER_LINE:
            lw = px(2) if st == "line" else px(1)
            c.create_rectangle(0, hh - lw, w, hh, fill=HEADER_LINE, outline="")
        if w < px(640):   # janela estreita: some com os enfeites para não cobrir o texto
            return
        if st == "timeline":
            _timeline(c, w, hh)
        else:
            _pins(c, w, hh)

    def retint():
        c.configure(bg=HEADER_BG)
        draw()
    c.bind("<Configure>", draw)
    c.retint = retint
    return c


def style_listbox(lb):
    if CLASSIC:   # campo afundado, branco, seleção azul-marinho
        lb.configure(bg=CARD, fg=TEXT, selectbackground=ACC, selectforeground=ACC_FG, relief="sunken", borderwidth=2,
                     highlightthickness=0, font=(F, fsize()), activestyle="none")
        return
    lb.configure(bg=CARD, fg=TEXT, selectbackground=ACC, selectforeground=ACC_FG, relief="flat",
                 highlightthickness=1, highlightbackground=LINE, highlightcolor=ACC, borderwidth=0,
                 font=(F, fsize()), activestyle="none")


# ---------- área de pré-visualização ----------
def gradient_image(w, h, corners):
    """Degradê suave entre os 4 cantos (sup-esq, sup-dir, inf-esq, inf-dir). Calculado em 1/4 do tamanho e ampliado."""
    sw, sh = max(2, w // 4), max(2, h // 4)
    u = np.linspace(0, 1, sw, dtype=np.float32)[None, :, None]
    v = np.linspace(0, 1, sh, dtype=np.float32)[:, None, None]
    tl, tr, bl, br = (np.array([int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], np.float32) for c in corners)
    arr = (tl * (1 - u) + tr * u) * (1 - v) + (bl * (1 - u) + br * u) * v
    return Image.fromarray(np.clip(arr + .5, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)


_stage = {}   # guarda a imagem do fundo (precisa de referência viva) e só refaz se o tema/tamanho mudar


def paint_stage(cv):
    """Desenha o fundo em degradê da área de pré-visualização (só nos temas com STAGE_GRAD).
    Chame logo depois de cv.delete('all'), antes de desenhar a folha."""
    if not STAGE_GRAD:
        return
    w, h = cv.winfo_width(), cv.winfo_height()
    if w < 4 or h < 4:
        return
    key = (NAME, w, h)
    if key not in _stage:
        from PIL import ImageTk
        _stage.clear()
        _stage[key] = ImageTk.PhotoImage(gradient_image(w, h, STAGE_GRAD))
    cv.create_image(0, 0, anchor="nw", image=_stage[key])


def empty_state(cv):
    """Estado vazio: círculo tracejado com marcas de corte (se ajusta ao tamanho da área)."""
    w, h = cv.winfo_width(), cv.winfo_height()
    r = max(20, min(px(70), min(w, h) // 5))
    x, y = w // 2, h // 2 - px(20)
    m = px(16)
    cv.create_oval(x - r, y - r, x + r, y + r, outline=STAGE_LINE, width=2, dash=(6, 5))
    cv.create_line(x - r - m, y, x + r + m, y, fill=STAGE_LINE)
    cv.create_line(x, y - r - m, x, y + r + m, fill=STAGE_LINE)
    t1 = cv.create_text(x, y + r + px(30), anchor="n", text="Selecione uma imagem com seus bottons", fill=STAGE_FG,
                        font=(F, fz(13), "bold"), width=max(100, w - px(40)), justify="center")
    y2 = (cv.bbox(t1) or (0, 0, 0, y + r + px(48)))[3] + px(6)
    cv.create_text(x, y2, anchor="n", text="Eles aparecem aqui já recortados e organizados na folha.", fill=STAGE_SUB,
                   font=(F, fz(10)), width=max(100, w - px(40)), justify="center")


# ---------- área com rolagem (barra lateral + roda do mouse) ----------
_AREAS, _INSTALLED, _INNERS = [], [], {}   # _INNERS: canvas -> [quadro interno, largura fixa, janela]


def _wheel(e):
    for root, outer, cv in _AREAS:
        try:
            w = root.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            continue
        if w is None:
            continue
        ws, os_ = str(w), str(outer)
        if ws == os_ or ws.startswith(os_ + "."):
            if w.winfo_class() in ("Listbox", "Text"):   # essas já rolam sozinhas
                return None
            up = getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0
            cv.yview_scroll(-1 if up else 1, "units")
            return "break"
    return None


def scrolled(parent, root, pad=14, width=None):
    """Painel com rolagem vertical. Devolve (contêiner, frame_interno): empacote o contêiner e coloque o conteúdo no interno."""
    outer = ttk.Frame(parent)
    cv = tk.Canvas(outer, highlightthickness=0, bd=0, bg=PANEL, yscrollincrement=px(20))
    if width:
        cv.configure(width=width)
    sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    cv.pack(side="left", fill="both", expand=True)
    inner = ttk.Frame(cv, padding=pad)
    win = cv.create_window((0, 0), window=inner, anchor="nw")

    def fit(_=None):
        cv.configure(scrollregion=(0, 0, inner.winfo_reqwidth(), inner.winfo_reqheight()))
        if not width:
            cv.configure(width=inner.winfo_reqwidth())   # a largura segue o conteúdo

    inner.bind("<Configure>", fit)
    cv.bind("<Configure>", lambda e: cv.itemconfigure(win, width=e.width))
    _AREAS.append((root, outer, cv))
    _INNERS[cv] = [inner, width, win]
    if not _INSTALLED:
        _INSTALLED.append(1)
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            root.bind_all(ev, _wheel, add="+")
            for cls in ("TCombobox", "TSpinbox"):   # roda sobre estes campos rola o painel (não muda o valor sem querer)
                root.bind_class(cls, ev, _wheel)
    return outer, inner


def rescale_areas(ratio):
    """Áreas com largura fixa (ex.: lista de tipos) acompanham a mudança do tamanho do texto."""
    for cv, v in _INNERS.items():
        if v[1]:
            v[1] = int(v[1] * ratio)
            cv.configure(width=v[1])


def refit_areas():
    """Depois de mudar a fonte, ajusta a largura (que segue o conteúdo) e a rolagem de cada área."""
    for cv, (inner, fixed, win) in list(_INNERS.items()):
        try:
            inner.update_idletasks()
            rw = inner.winfo_reqwidth()
            if not fixed:
                cv.configure(width=rw)
                cv.itemconfigure(win, width=rw)
            cv.configure(scrollregion=(0, 0, rw if not fixed else max(rw, cv.winfo_width()), inner.winfo_reqheight()))
        except tk.TclError:
            pass


def rescale_wraps(root, ratio):
    """Multiplica a largura de quebra de linha de todos os textos já criados (mantém as mesmas linhas em tela)."""
    def walk(w):
        for c in w.winfo_children():
            if c.winfo_class() in ("TLabel", "Label"):
                try:
                    wl = int(float(str(c.cget("wraplength"))))
                except (ValueError, tk.TclError):
                    wl = 0
                if wl > 0:
                    c.configure(wraplength=max(1, int(round(wl * ratio))))
            walk(c)
    walk(root)


def retint_areas():
    """Recolore o fundo das áreas com rolagem depois de trocar o tema."""
    for _, _, cv in _AREAS:
        cv.configure(bg=PANEL)


def retint_popdowns(root):
    """Recolore a lista suspensa (já criada) de cada caixa de seleção."""
    def walk(w):
        for c in w.winfo_children():
            if c.winfo_class() == "TCombobox":
                try:
                    pd = root.tk.call("ttk::combobox::PopdownWindow", str(c))
                    root.tk.call(f"{pd}.f.l", "configure", "-background", CARD, "-foreground", TEXT,
                                 "-selectbackground", ACC, "-selectforeground", ACC_FG,
                                 "-font", (F, fsize()))
                except tk.TclError:
                    pass
            walk(c)
    walk(root)
