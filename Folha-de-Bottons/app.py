"""Interface (Tkinter). Execute: python app.py"""


import os
import sys


def _relaunch_windowless():
    """Windows: reabre o programa com pythonw.exe (sem console) e encerra esta cópia, antes dos imports
    pesados, para o prompt sumir quase na hora. Para depurar com o prompt visível: python app.py --console"""
    if os.name != "nt" or "--console" in sys.argv or getattr(sys, "frozen", False):
        return False
    exe = sys.executable
    if os.path.basename(exe).lower() != "python.exe":   # já é pythonw.exe (.pyw): nada a fazer
        return False
    pw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if not os.path.exists(pw):
        return False
    try:
        import subprocess
        subprocess.Popen([pw, os.path.abspath(__file__)] + sys.argv[1:], cwd=os.getcwd(),
                         creationflags=0x00000008 | 0x00000200 | 0x08000000)  # DETACHED | NEW_GROUP | NO_WINDOW
        return True
    except Exception:
        return False


def _hide_console():
    """Plano B: esconde a janela do console, se ela pertencer só a este programa."""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        procs = (ctypes.c_uint * 4)()
        if k32.GetConsoleProcessList(procs, 4) == 1:   # só o Python usa este console (não é um terminal seu)
            h = k32.GetConsoleWindow()
            if h:
                ctypes.windll.user32.ShowWindow(h, 0)  # SW_HIDE
    except Exception:
        pass


if __name__ == "__main__":
    if _relaunch_windowless():
        sys.exit(0)
    if "--console" not in sys.argv:
        _hide_console()

import datetime
import json
import random
import tkinter as tk
import tempfile
import time
import traceback
import audio
from tkinter import ttk, filedialog, colorchooser, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
from detect import detect_circles
from process import make_button, trim_margin, auto_color, mm, open_sheet
import theme
import cdplayer
import ajuda
from layout import SHEETS, build_pages, export, positions, grid_size
from groups import signature, distance, cluster, TOL


PREVIEW_DPI = 120   # resolução da prévia na tela (zoom 100%); a exportação/impressão usa o DPI escolhido (900/600)
BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "erro_folha_bottons.log")
CFG = os.path.join(BASE, "config_folha_bottons.json")   # guarda o tema escolhido


def load_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cfg(cfg):
    try:
        with open(CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def log_error(txt):
    """Sem o prompt, os erros não aparecem em lugar nenhum: guarda num arquivo de log ao lado do programa."""
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ---\n{txt}\n")
    except OSError:
        pass


def crash(exc, val, tb):
    """Erro fora da interface (ex.: ao iniciar): registra e mostra uma janela."""
    log_error("".join(traceback.format_exception(exc, val, tb)))
    try:
        r = tk.Tk(); r.withdraw()
        messagebox.showerror("Folha de Bottons", f"Ocorreu um erro:\n\n{val}\n\nDetalhes salvos em:\n{LOG}")
        r.destroy()
    except Exception:
        pass


class App(tk.Tk):
    shown_errors = set()

    def report_callback_exception(s, exc, val, tb):
        """Erro dentro de um botão/evento: registra e avisa (uma vez por tipo de erro, para não repetir janelas)."""
        log_error("".join(traceback.format_exception(exc, val, tb)))
        key = f"{exc.__name__}: {val}"
        if key not in App.shown_errors:
            App.shown_errors.add(key)
            messagebox.showerror("Folha de Bottons", f"Ocorreu um erro:\n\n{key}\n\nDetalhes salvos em:\n{LOG}")

    def __init__(s):
        super().__init__()
        s.title("Folha de Bottons")
        s.audio = audio.AudioManager()
        s.protocol("WM_DELETE_WINDOW", s.close_app)
        cfg = load_cfg()
        theme.set_text_scale(cfg.get("tamanho_texto"))         # tamanho do texto da última vez (acessibilidade)
        theme.set_contrast(bool(cfg.get("alto_contraste")))    # alto contraste da última vez
        theme.set_theme(cfg.get("tema"))   # tema da última vez (já sai com o contraste escolhido)
        s.music_enabled = tk.BooleanVar(value=cfg.get("musica", True))
        s.click_enabled = tk.BooleanVar(value=cfg.get("som_click", True))
        s.music_volume = tk.DoubleVar(value=cfg.get("volume_musica", audio.AudioManager.DEFAULT_VOLUME))
        s.audio.music_enabled = s.music_enabled.get()
        s.audio.click_enabled = s.click_enabled.get()
        s.audio.music_volume = s.music_volume.get()
        s.audio.use_files(cfg.get("musica_arquivo"), cfg.get("efeito_arquivo"))   # música/efeito escolhidos da última vez
        s.music_file = tk.StringVar()
        s.click_file = tk.StringVar()
        s.cd = None   # leitor estilo "CD Player": só é criado quando o tema é o Windows 95 clássico
        s.cd_shuffle = tk.BooleanVar(value=cfg.get("player_aleatorio", False))
        s.cd_repeat = tk.BooleanVar(value=cfg.get("player_repetir", False))
        s.cd_view = tk.StringVar(value=cfg.get("player_exibir", "decorrido"))   # "decorrido" | "restante"
        s.text_size = tk.StringVar(value=next((k for k, v in theme.TEXT_SIZES.items() if v == theme.TEXT_SCALE), "Normal (100%)"))
        s.high_contrast = tk.BooleanVar(value=theme.CONTRAST)
        s.tick_errors = set()
        s.audio.start_music()
        theme.apply(s)
        s.tema = tk.StringVar(value=theme.NAME)
        s.fit_window()
        s.hdr = theme.header(s, "Folha de Bottons", "Detecte, recorte e organize seus pins para impressão")
        s.hdr.pack(side="top", fill="x")
        # As imagens carregadas ficam em s.sources. Cada item também guarda a sua própria
        # imagem de origem, permitindo combinar várias folhas sem perder a referência da arte.
        s.sources, s.active_source = [], 0
        s.src, s.items, s.bgcolor, s.photo = None, [], "#ffffff", None
        s.source_var = tk.StringVar()
        s.prevs, s.page, s.prev = [], 0, None
        s.shownum, s.geom = False, None
        s.print_state = {}   # impressora/configurações escolhidas no diálogo do Windows (valem até fechar o programa)
        s.zoom, s.px, s.py, s.drag = 1.0, 0.0, 0.0, None
        s._click_start = None
        s._click_moved = False
        s.hi, s.hijob, s.ver = None, None, 0  # pré-visualização em alta resolução (sob zoom)
        # Estado do aviso visual da próxima página. O alerta só começa quando uma nova
        # divisão em páginas é criada; ao clicar na seta ele é encerrado imediatamente.
        s._next_blink_job = None
        s._next_blink_on = False
        s._next_blink_dismissed = False
        s._button_cache = {}       # cache permanente das artes renderizadas
        s._signature_cache = {}     # miniaturas usadas no agrupamento; independem da tolerância
        s._adjust_type_job = None  # atualiza miniaturas/grupos depois que a sequência de ajustes termina
        # Estado da pré-visualização: a imagem exibida é um "tile" maior que a janela.
        # Pan só move o tile no Canvas; crop/resize só acontece quando o tile precisa ser renovado.
        s._view_item = None
        s._view_buffer = 220
        s._view_job = None
        s._view_force_key = None
        s._view_key = None
        s._view_size = (0, 0)
        s._view_zoom = 1.0
        s._resize_job = None
        s._settle_job = None       # render de qualidade total, logo depois que o zoom/rolagem para
        s._tile_pan = (0.0, 0.0)   # (px, py) no momento em que o desenho atual da folha foi feito
        s.size = tk.IntVar(value=32)
        s.trim = tk.BooleanVar(value=True)
        s.gap = tk.StringVar(value="3")
        s.sheet = tk.StringVar(value="A4")
        s.cw, s.ch = tk.StringVar(value="210"), tk.StringVar(value="297")
        s.bg = tk.StringVar(value="branco")
        s.dpi = tk.StringVar(value="900")
        s.align = tk.StringVar(value="center")   # "center" | "topleft" (canto sup. esquerdo)
        s.qty, s.qvars, s.thumbs, s.qjob = {}, {}, [], None   # quantidade por tipo (grupo)
        s.tol = tk.DoubleVar(value=TOL)
        s.nb = ttk.Notebook(s)
        s.nb.pack(side="left", fill="y")
        box1, L = theme.scrolled(s.nb, s)     # aba 1 com barra de rolagem
        s.nb.add(box1, text="Bottons")
        Q = ttk.Frame(s.nb, padding=14)
        s.nb.add(Q, text="Quantidades")
        box3, C = theme.scrolled(s.nb, s)     # aba de configurações com barra de rolagem
        s.nb.add(box3, text="Configurações")
        s.build_settings(C)
        box4, HP = theme.scrolled(s.nb, s)      # aba de ajuda com barra de rolagem
        s.nb.add(box4, text="Ajuda")
        s.help_tab = box4
        ajuda.build_help(HP, s)
        tip, wl = ajuda.Tooltip, theme.wrap(250)
        src_row = ttk.Frame(L)
        src_row.pack(fill="x")
        w_ = ttk.Button(src_row, text="Selecionar imagem", style="Accent.TButton", command=s.open)
        w_.pack(side="left", fill="x", expand=True, padx=(0, 3))
        tip(w_, "Escolha uma ou várias imagens de uma vez. As imagens escolhidas substituem as folhas carregadas.")
        w_ = ttk.Button(src_row, text="+ Adicionar folhas", command=s.add_sources)
        w_.pack(side="left", fill="x", expand=True, padx=(3, 0))
        tip(w_, "Escolha outras folhas de bottons para acrescentar à seleção atual, sem apagar o que já foi carregado.")
        src_row2 = ttk.Frame(L)
        src_row2.pack(fill="x", pady=(3, 0))
        ttk.Label(src_row2, text="Folha ativa para ajustes manuais:").pack(side="left")
        s.source_cb = ttk.Combobox(src_row2, textvariable=s.source_var, state="readonly", width=18)
        s.source_cb.pack(side="left", fill="x", expand=True, padx=(6, 0))
        s.source_cb.bind("<<ComboboxSelected>>", s.on_source_selected)
        ttk.Button(src_row2, text="Limpar", width=7, command=s.clear_sources).pack(side="left", padx=(6, 0))
        tip(s.source_cb, "Quando houver várias folhas, escolha aqui qual imagem será usada no botão 'Adicionar' para marcar um botton manualmente.")
        s.sources_lbl = ttk.Label(L, style="Info.TLabel", wraplength=wl, justify="left")
        s.sources_lbl.pack(anchor="w", pady=(2, 0))
        s.step_lbl = ttk.Label(L, style="Info.TLabel", wraplength=wl, justify="left")
        s.step_lbl.pack(anchor="w", pady=(4, 0))
        w_ = ttk.Checkbutton(L, text="Cortar margem em branco ao detectar", variable=s.trim, command=s.option_toggle)
        w_.pack(anchor="w", pady=(4, 0))
        tip(w_, "Se houver uma borda branca em volta da arte, ela é removida para o botton não sair com aro branco.")
        ttk.Label(L, style="Sec.TLabel", text="Tamanho do botton").pack(anchor="w", pady=(8, 0))
        for v, t_ in ((32, "32 mm — arte / 42 mm total"), (58, "58 mm — arte / 68 mm total")):
            w_ = ttk.Radiobutton(L, text=t_, value=v, variable=s.size, command=s.option_refresh)
            w_.pack(anchor="w")
            tip(w_, "O número é o tamanho da arte. O programa soma um contorno de 5 mm por lado; o tamanho total é o que ocupa espaço na folha.")
        ttk.Label(L, style="Sec.TLabel", text="Espaçamento entre bottons (mm)").pack(anchor="w", pady=(8, 0))
        w_ = ttk.Entry(L, textvariable=s.gap)
        w_.pack(fill="x")
        tip(w_, "Distância entre um botton e outro. Quanto menor, mais bottons cabem na folha. Com 0 eles ficam encostados e pode caber uma coluna a mais.")
        ttk.Label(L, style="Info.TLabel", wraplength=wl, justify="left",
                  text="Menos espaço = mais bottons por folha. Com 0 eles ficam encostados e pode caber uma coluna a mais.").pack(anchor="w")
        ttk.Label(L, style="Sec.TLabel", text="Folha").pack(anchor="w", pady=(8, 0))
        cb = ttk.Combobox(L, textvariable=s.sheet, values=list(SHEETS) + ["Personalizado"], state="readonly")
        cb.pack(fill="x")
        tip(cb, "Tamanho do papel. Escolha “Personalizado” para digitar largura e altura em milímetros.")
        f = ttk.Frame(L)
        f.pack(fill="x")
        ttk.Entry(f, textvariable=s.cw, width=6).pack(side="left")
        ttk.Label(f, text=" x ").pack(side="left")
        ttk.Entry(f, textvariable=s.ch, width=6).pack(side="left")
        ttk.Label(f, text=" mm").pack(side="left")
        ttk.Label(L, style="Sec.TLabel", text="Posição dos bottons na folha").pack(anchor="w", pady=(8, 0))
        for v, t_, h_ in (("center", "Centralizados", "O bloco de bottons fica no meio da folha, com margem de 5 mm."),
                          ("topleft", "Canto superior (cabe mais bottons)",
                           "Começa no canto superior esquerdo e usa só 3 mm de folga nas bordas, o que pode encaixar uma coluna ou linha a mais "
                           "(ex.: 3 bottons de 58 mm na A4, com espaçamento 0). Se a impressora cortar as bordas, use Centralizados.")):
            w_ = ttk.Radiobutton(L, text=t_, value=v, variable=s.align, command=s.option_refresh)
            w_.pack(anchor="w")
            tip(w_, h_)
        s.fit = ttk.Label(L, style="Info.TLabel", wraplength=wl, justify="left")
        s.fit.pack(anchor="w", pady=(4, 0))
        s.fit_tip = ttk.Label(L, style="Sec.TLabel", wraplength=wl, justify="left")
        s.fit_tip.pack(anchor="w")
        ttk.Label(L, style="Sec.TLabel", text="Fundo").pack(anchor="w", pady=(8, 0))
        bb = ttk.Combobox(L, textvariable=s.bg, values=["branco", "transparente", "personalizado"], state="readonly")
        bb.pack(fill="x")
        tip(bb, "Cor do fundo da folha. “Transparente” só vale para PNG; no PDF vira branco.")
        ttk.Label(L, style="Sec.TLabel", text="DPI de exportação").pack(anchor="w", pady=(8, 0))
        dpi_cb = ttk.Combobox(L, textvariable=s.dpi, values=["900", "600"], state="readonly")
        dpi_cb.pack(fill="x")
        tip(dpi_cb, "Qualidade da exportação e da impressão. 900 é a máxima nitidez, mas o arquivo fica bem maior e demora mais; 600 é mais leve e já fica muito nítido.")
        for w in (cb, bb, dpi_cb):
            w.bind("<<ComboboxSelected>>", s.on_combo)
        for v in (s.gap, s.cw, s.ch):
            v.trace_add("write", lambda *a: s.after(400, s.refresh))
        ttk.Label(L, style="Sec.TLabel", text="Bottons detectados").pack(anchor="w", pady=(10, 0))
        s.lb = tk.Listbox(L, height=7, exportselection=False)
        theme.style_listbox(s.lb)
        s.lb.pack(fill="x")
        s.lb.bind("<<ListboxSelect>>", lambda e: s.update_selhint())
        s.selhint = ttk.Label(L, style="Info.TLabel", wraplength=wl, justify="left")
        s.selhint.pack(anchor="w")
        r1 = ttk.Frame(L); r1.pack(fill="x", pady=2)
        for t_, c_, h_ in (("Adicionar", s.add, "Adiciona um botton que o programa não detectou: na imagem, arraste do centro dele até a borda."),
                           ("Remover", s.remove, "Tira da folha o botton selecionado na lista."),
                           ("▲", lambda: s.move(-1), "Sobe o botton selecionado na lista (muda a ordem e a numeração)."),
                           ("▼", lambda: s.move(1), "Desce o botton selecionado na lista (muda a ordem e a numeração).")):
            w_ = ttk.Button(r1, text=t_, width=8 if len(t_) > 1 else 3, command=c_)
            w_.pack(side="left")
            tip(w_, h_)
        ttk.Label(L, style="Info.TLabel", text="Ajustar o recorte do botton selecionado:").pack(anchor="w", pady=(6, 0))
        r2 = ttk.Frame(L); r2.pack(fill="x", pady=2)
        for t_, k, d, h_ in (("◀", "cx", -1, "Mover o recorte para a esquerda"), ("▶", "cx", 1, "Mover o recorte para a direita"),
                             ("▲", "cy", -1, "Mover o recorte para cima"), ("▼", "cy", 1, "Mover o recorte para baixo"),
                             ("+", "r", -1, "Aproximar: círculo menor, a arte aparece maior"),
                             ("−", "r", 1, "Afastar: círculo maior, aparece mais da imagem em volta"),
                             ("⟲", "rot", -5, "Girar 5° para a esquerda"), ("⟳", "rot", 5, "Girar 5° para a direita")):
            w_ = ttk.Button(r2, text=t_, width=3, style="Mini.TButton", command=lambda k=k, d=d: s.adj(k, d))
            w_.pack(side="left")
            tip(w_, h_)
        r3 = ttk.Frame(L); r3.pack(fill="x", pady=2)
        w_ = ttk.Button(r3, text="Cor do contorno", command=s.pick)
        w_.pack(side="left")
        tip(w_, "Escolhe manualmente a cor do contorno de 5 mm do botton selecionado.")
        w_ = ttk.Button(r3, text="🎲", width=3, command=s.palette_picker)
        w_.pack(side="left", padx=(4, 0))
        tip(w_, "🎲 Pega as 5 principais cores do botton selecionado para você escolher rapidamente a cor do contorno.")
        w_ = ttk.Button(r3, text="Conta-gotas", command=s.eyedropper)
        w_.pack(side="left", padx=(4, 0))
        tip(w_, "Abre um conta-gotas: passe o mouse sobre a imagem e clique para usar exatamente aquela cor no contorno.")
        w_ = ttk.Button(r3, text="Cor automática", command=s.reset_color)
        w_.pack(side="left")
        tip(w_, "Volta à cor calculada a partir da borda da arte.")
        w_ = ttk.Button(L, text="Cortar margem do selecionado", command=s.trim_sel)
        w_.pack(fill="x")
        tip(w_, "Remove a borda branca em volta da arte do botton selecionado.")
        s.numbtn = ttk.Button(L, text="Mostrar numeração (#)", command=s.toggle_nums)
        s.numbtn.pack(fill="x", pady=(4, 0))
        tip(s.numbtn, "Mostra sobre a folha o número (#1, #2...) de cada botton, para você achar o da lista.")
        nav = ttk.Frame(L); nav.pack(fill="x", pady=(10, 0))
        s.nbp = ttk.Button(nav, text="◀ Página", command=lambda: s.nav(-1))
        s.nbp.pack(side="left")
        s.nbn = ttk.Button(nav, text="Página ▶", command=lambda: s.nav(1))
        s.nbn.pack(side="left")
        tip(s.nbp, "Página anterior (PgUp). Quando os bottons não cabem em uma folha, o programa cria mais páginas.")
        tip(s.nbn, "Próxima página (PgDn). Quando os bottons não cabem em uma folha, o programa cria mais páginas.")
        zf = ttk.Frame(L); zf.pack(fill="x", pady=(8, 0))
        w_ = ttk.Label(zf, text="Zoom", style="Sec.TLabel")
        w_.pack(side="left")
        tip(w_, "Ctrl + roda do mouse: zoom no ponto do cursor. Roda: rolar para cima/baixo. Shift + roda: rolar para os lados. "
                "Arrastar (com zoom): mover.")
        ttk.Button(zf, text="−", width=3, style="Mini.TButton", command=lambda: s.zoom_btn(1 / 1.25)).pack(side="left", padx=(8, 0))
        s.zlbl = ttk.Label(zf, text="100%", width=6, anchor="center")
        s.zlbl.pack(side="left")
        ttk.Button(zf, text="+", width=3, style="Mini.TButton", command=lambda: s.zoom_btn(1.25)).pack(side="left")
        w_ = ttk.Button(zf, text="Ajustar", style="Mini.TButton", command=s.zoom_reset)
        w_.pack(side="left", padx=(6, 0))
        tip(w_, "Volta ao zoom que mostra a folha inteira (duplo clique na folha também).")
        s.info = ttk.Label(L, style="Info.TLabel", text="", wraplength=wl, justify="left")
        s.info.pack(anchor="w", pady=(4, 0))
        ex = ttk.Frame(L); ex.pack(fill="x", pady=(12, 0))
        w_ = ttk.Button(ex, text="Exportar", style="Accent.TButton", command=s.export)
        w_.pack(side="left", fill="x", expand=True, padx=(0, 3))
        tip(w_, "Salva a folha em PDF (todas as páginas em um arquivo) ou PNG (um arquivo por página).")
        w_ = ttk.Button(ex, text="Imprimir", style="Accent.TButton", command=s.print_sheet)
        w_.pack(side="left", fill="x", expand=True, padx=(3, 0))
        tip(w_, "Abre as opções de impressão. Imprima sempre em 100% / Tamanho real.")
        # Lado direito: a folha em cima e, EMBAIXO dela, a barra de página/zoom. A barra não fica mais por cima da folha:
        # com letras grandes ela crescia e escondia os bottons.
        s.stage = ttk.Frame(s)
        s.stage.pack(side="right", fill="both", expand=True)
        s.pgbar = ttk.Frame(s.stage, padding=(8, 4))
        s.pgbar.pack(side="bottom", fill="x")   # empacotada ANTES da folha: o espaço dela está sempre reservado
        s.cv = tk.Canvas(s.stage, bg=theme.STAGE, highlightthickness=0)
        s.cv.pack(side="top", fill="both", expand=True)
        s.cv.bind("<Configure>", s.canvas_configure)
        s.pg_nav = ttk.Frame(s.pgbar)
        s.pg_prev = ttk.Button(s.pg_nav, text="◀", width=3, style="Mini.TButton", command=lambda: s.nav(-1))
        s.pg_lbl = ttk.Label(s.pg_nav, style="Sec.TLabel", width=16, anchor="center", text="Sem folha")
        s.pg_next = ttk.Button(s.pg_nav, text="▶", width=3, style="Mini.TButton", command=lambda: s.nav(1))
        s.pg_prev.pack(side="left"); s.pg_lbl.pack(side="left", padx=4); s.pg_next.pack(side="left")
        s.pg_tools = ttk.Frame(s.pgbar)
        s.zbtn = ttk.Button(s.pg_tools, text="100%", width=6, style="Mini.TButton", command=s.zoom_reset)
        s.fsbtn = ttk.Button(s.pg_tools, text="⛶ Tela cheia", command=s.toggle_fullscreen)
        s.zbtn.pack(side="left"); s.fsbtn.pack(side="left", padx=(8, 0))
        s.pgbar.columnconfigure(1, weight=1)
        s.pg_nav.grid(row=0, column=0, sticky="w")
        s.pg_tools.grid(row=0, column=1, sticky="e")
        s.pgbar.bind("<Configure>", s.layout_pgbar)
        tip(s.fsbtn, "Pré-visualização em tela cheia (F11). Esc sai.")
        tip(s.zbtn, "Zoom atual. Clique para ajustar a folha inteira à tela. Ctrl + roda do mouse: zoom no ponto do cursor · "
                    "Roda: rolar · Shift + roda: rolar para os lados · Arrastar: mover.")
        tip(s.pg_lbl, "Quando os bottons não cabem em uma folha, o programa cria mais páginas. Troque com ◀ ▶ ou PgUp/PgDn.")
        s.bind("<F1>", lambda e: s.nb.select(s.help_tab))
        s.bind("<Prior>", lambda e: s.key_nav(-1)); s.bind("<Next>", lambda e: s.key_nav(1))
        s.cv.bind("<Left>", lambda e: s.key_nav(-1)); s.cv.bind("<Right>", lambda e: s.key_nav(1))
        s.bind("<F11>", s.toggle_fullscreen)
        s.bind("<Escape>", s.exit_fullscreen)
        s.cv.bind("<MouseWheel>", s.wheel)                      # Windows / macOS
        s.cv.bind("<Button-4>", s.wheel); s.cv.bind("<Button-5>", s.wheel)  # Linux
        s.cv.bind("<ButtonPress-1>", s.pan_start)
        s.cv.bind("<B1-Motion>", s.pan_move)
        s.cv.bind("<ButtonRelease-1>", s.pan_end_click)
        s.cv.bind("<ButtonPress-2>", s.pan_start); s.cv.bind("<B2-Motion>", s.pan_move); s.cv.bind("<ButtonRelease-2>", s.pan_end)   # botão do meio
        s.cv.bind("<Double-Button-1>", lambda e: s.zoom_reset())
        s.bind("<Control-plus>", lambda e: s.zoom_btn(1.25)); s.bind("<Control-equal>", lambda e: s.zoom_btn(1.25))
        s.bind("<Control-minus>", lambda e: s.zoom_btn(1 / 1.25)); s.bind("<Control-0>", lambda e: s.zoom_reset())
        s.build_tab_qty(Q)
        s.after(300, s.audio_tick)
        s.update_fit()
        s.update_step()
        s.update_selhint()
        if theme.TEXT_SCALE > 1:
            s.after(150, s.make_room)   # texto grande: garante espaço para a pré-visualização
        s.after(700, s.maybe_intro)   # primeira vez: mostra a introdução

    def build_settings(s, parent):
        s.audio_box = parent
        ttk.Label(parent, text="Aparência", style="Sec.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="Tema").pack(anchor="w")
        tc = ttk.Combobox(parent, textvariable=s.tema, values=list(theme.THEMES), state="readonly")
        tc.pack(fill="x", pady=(0, 10))
        tc.bind("<<ComboboxSelected>>", s.change_theme)
        # acessibilidade: letras maiores e alto contraste (valem para todo o programa e para qualquer tema)
        ttk.Label(parent, text="Tamanho do texto").pack(anchor="w")
        for label in theme.TEXT_SIZES:
            w_ = ttk.Radiobutton(parent, text=label, value=label, variable=s.text_size, command=s.change_text_size)
            w_.pack(anchor="w")
            ajuda.Tooltip(w_, "Aumenta todas as letras do programa de uma vez. A escolha fica salva.")
        w_ = ttk.Checkbutton(parent, text="Alto contraste", variable=s.high_contrast, command=s.change_contrast)
        w_.pack(anchor="w", pady=(10, 0))
        ajuda.Tooltip(w_, "Letras em preto ou branco puro, bordas mais marcadas e sem transparência. Funciona com qualquer tema.")
        ttk.Label(parent, text="Alto contraste deixa letras e bordas mais fortes e fáceis de ler, em qualquer tema.",
                  style="Info.TLabel", wraplength=theme.wrap(270), justify="left").pack(anchor="w", pady=(4, 14))
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(0, 14))
        ttk.Label(parent, text="Áudio", style="Sec.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(parent, text="Ativar música de fundo", variable=s.music_enabled, command=s.toggle_music).pack(anchor="w")
        s.music_lbl = ttk.Label(parent, text="Música")
        s.music_lbl.pack(anchor="w", pady=(10, 2))
        s.music_cb = ttk.Combobox(parent, textvariable=s.music_file, state="readonly")
        s.music_cb.pack(fill="x")
        s.music_cb.bind("<<ComboboxSelected>>", s.change_music_file)
        s.vol_title = ttk.Label(parent, text="Volume da música")
        s.vol_title.pack(anchor="w", pady=(10, 2))
        vol = ttk.Scale(parent, from_=0, to=100, variable=s.music_volume, command=s.change_music_volume)
        vol.pack(fill="x")
        s.vol_label = ttk.Label(parent, text=f"{int(s.music_volume.get())}%", style="Info.TLabel")
        s.vol_label.pack(anchor="e")
        ttk.Checkbutton(parent, text="Ativar som de clique", variable=s.click_enabled, command=s.toggle_click).pack(anchor="w", pady=(8, 0))
        ttk.Label(parent, text="Efeito de clique").pack(anchor="w", pady=(10, 2))
        s.click_cb = ttk.Combobox(parent, textvariable=s.click_file, state="readonly")
        s.click_cb.pack(fill="x")
        s.click_cb.bind("<<ComboboxSelected>>", s.change_click_file)
        ttk.Button(parent, text="Atualizar listas", command=s.refresh_audio_lists).pack(fill="x", pady=(10, 4))
        row = ttk.Frame(parent)
        row.pack(fill="x")
        ttk.Button(row, text="Abrir pasta musica", command=lambda: s.open_folder(s.audio.music_dir)).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(row, text="Abrir pasta efeito", command=lambda: s.open_folder(s.audio.click_dir)).pack(side="left", expand=True, fill="x", padx=(3, 0))
        ttk.Label(parent, text="Coloque arquivos MP3 ou WAV nas pastas \"musica\" e \"efeito\" (ao lado do programa) e toque em \"Atualizar listas\".",
                  style="Info.TLabel", wraplength=theme.wrap(270)).pack(anchor="w", pady=(8, 0))
        ttk.Label(parent, text="As alterações são salvas automaticamente.", style="Info.TLabel", wraplength=theme.wrap(270)).pack(anchor="w", pady=(10, 0))
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(16, 8))
        ttk.Label(parent, text="idealizado por Ber-nuh e feito inteiramente pela IA!", style="Info.TLabel",
                  wraplength=theme.wrap(270), justify="left").pack(anchor="w", pady=(0, 6))
        s.refresh_audio_lists()
        s.update_cd_player()

    def update_cd_player(s):
        """Tema Windows 95 clássico: o leitor estilo CD Player substitui a caixa "Música". Outros temas: caixa normal."""
        if theme.CD_PLAYER:
            if s.cd is None:
                s.cd = cdplayer.CDPlayer(s.audio_box, s)
            s.music_lbl.pack_forget()
            s.music_cb.pack_forget()
            s.cd.pack(fill="x", pady=(8, 0), before=s.vol_title)
            s.cd.reload()
            theme.retint_popdowns(s)
        elif s.cd is not None:
            s.cd.pack_forget()
            s.music_lbl.pack(anchor="w", pady=(10, 2), before=s.vol_title)
            s.music_cb.pack(fill="x", before=s.vol_title)

    def music_advance(s, step=1, auto=False):
        """Vai para outra música da pasta: step=1 próxima, -1 anterior. auto=True: a música acabou sozinha."""
        names = s.audio.list_music()
        if not names:
            return
        cur = s.audio.music_name()
        i = names.index(cur) if cur in names else -1
        if auto and s.cd_repeat.get():
            j = max(i, 0)
        elif step > 0 and s.cd_shuffle.get() and len(names) > 1:
            j = random.choice([k for k in range(len(names)) if k != i])
        else:
            j = (i + step) % len(names)
        if names[j] == cur:
            s.audio.restart_music()   # só há uma música (ou repetir): toca de novo
        else:
            s.music_file.set(names[j])
            s.change_music_file()
        if s.cd is not None:
            s.cd.refresh_display()

    def audio_tick(s):
        """A cada 0,3 s: quando a música termina, repete a mesma faixa (todos os temas, exceto o Windows 95)
        ou segue as regras do leitor estilo CD Player (próxima faixa / aleatório / repetir). Atualiza o visor do leitor."""
        try:
            if s.audio.music_ended():
                if theme.CD_PLAYER:
                    s.music_advance(1, auto=True)   # só o leitor do tema Windows 95 passa para outra faixa sozinho
                else:
                    s.audio.restart_music()         # demais temas: a música fica em loop
            if s.cd is not None and s.cd.winfo_ismapped():
                s.cd.refresh_display()
        except Exception:
            err = traceback.format_exc()
            if err not in s.tick_errors:   # registra cada tipo de erro uma vez só, sem encher o log
                s.tick_errors.add(err)
                log_error(err)
        s.after(300, s.audio_tick)

    def save_audio_config(s):
        cfg = load_cfg()
        cfg.update({"tema": theme.NAME, "musica": bool(s.music_enabled.get()), "som_click": bool(s.click_enabled.get()), "volume_musica": int(round(s.music_volume.get())),
                    "player_aleatorio": bool(s.cd_shuffle.get()), "player_repetir": bool(s.cd_repeat.get()), "player_exibir": s.cd_view.get()})
        if s.music_file.get():
            cfg["musica_arquivo"] = s.music_file.get()
        if s.click_file.get():
            cfg["efeito_arquivo"] = s.click_file.get()
        save_cfg(cfg)

    def refresh_audio_lists(s):
        """Relê as pastas "musica" e "efeito" e atualiza as duas listas de escolha."""
        for cb, var, names, cur in ((s.music_cb, s.music_file, s.audio.list_music(), s.audio.music_name()),
                                    (s.click_cb, s.click_file, s.audio.list_effects(), s.audio.click_name())):
            cb.configure(values=names, state="readonly" if names else "disabled")
            var.set(cur if cur in names else (names[0] if names else ""))
        if s.cd is not None and theme.CD_PLAYER:
            s.cd.reload()
        theme.retint_popdowns(s)

    def open_folder(s, path):
        try:
            os.makedirs(path, exist_ok=True)
            os.startfile(path)
        except (OSError, AttributeError):
            messagebox.showinfo("Folha de Bottons", f"Pasta:\n{path}")

    def change_music_file(s, e=None):
        prev, name = s.audio.music_name(), s.music_file.get()
        if name == prev:
            return
        if not s.audio.set_music_file(name):
            messagebox.showwarning("Folha de Bottons", f"O Windows não conseguiu abrir este arquivo de música:\n{name}\n\nTente MP3 ou WAV.")
            s.audio.set_music_file(prev)
            s.music_file.set(prev)
            return
        s.save_audio_config()

    def change_click_file(s, e=None):
        prev, name = s.audio.click_name(), s.click_file.get()
        if not s.audio.set_click_file(name):
            messagebox.showwarning("Folha de Bottons", f"O Windows não conseguiu abrir este efeito:\n{name}\n\nTente MP3 ou WAV.")
            s.audio.set_click_file(prev)
            s.click_file.set(prev)
            return
        s.save_audio_config()
        s.audio.play_click(force=True)   # prévia do efeito escolhido

    def toggle_music(s):
        s.audio.set_music_enabled(s.music_enabled.get())
        s.save_audio_config()
        s.audio.play_click() if s.click_enabled.get() else None

    def toggle_click(s):
        s.audio.set_click_enabled(s.click_enabled.get())
        s.save_audio_config()
        if s.click_enabled.get():
            s.audio.play_click()

    def change_music_volume(s, value=None):
        s.audio.set_music_volume(s.music_volume.get())
        if hasattr(s, "vol_label"):
            s.vol_label.configure(text=f"{int(round(s.music_volume.get()))}%")
        s.save_audio_config()

    def option_refresh(s):
        s._clear_button_cache()
        s.audio.play_click()
        s.refresh()

    def option_toggle(s):
        s.audio.play_click()

    def close_app(s):
        try:
            s.audio.stop()
        finally:
            s.destroy()

    def change_theme(s, e=None):
        s.audio.play_click()
        theme.set_theme(s.tema.get())
        cfg = load_cfg(); cfg["tema"] = theme.NAME; save_cfg(cfg)
        s.retheme()

    def retheme(s):
        """Aplica as cores do tema atual a tudo que já está na tela."""
        theme.apply(s)
        s.hdr.retint()
        s.cv.configure(bg=theme.STAGE)
        theme.style_listbox(s.lb)
        theme.retint_areas()
        theme.retint_popdowns(s)
        s.build_types()
        s._invalidate_view()
        s.show()
        s.update_cd_player()
        s.after(80, s.layout_pgbar)

    # ---------- acessibilidade: tamanho do texto e alto contraste ----------
    def save_view_config(s):
        cfg = load_cfg()
        cfg.update({"tema": theme.NAME, "tamanho_texto": theme.TEXT_SCALE, "alto_contraste": theme.CONTRAST})
        save_cfg(cfg)

    def change_text_size(s):
        """Aplica o tamanho de texto escolhido na hora, sem reiniciar: fontes, quebras de linha e áreas com rolagem."""
        new = theme.TEXT_SIZES.get(s.text_size.get(), 1.0)
        old = theme.TEXT_SCALE
        if abs(new - old) < 1e-6:
            return
        s.audio.play_click()
        theme.set_text_scale(new)
        s.save_view_config()
        s.config(cursor="watch")
        s.update_idletasks()
        try:
            theme.rescale_wraps(s, new / old)    # textos que quebram linha acompanham o tamanho das letras
            theme.rescale_areas(new / old)       # listas de largura fixa (aba Quantidades)
            if s.cd is not None:                 # o leitor de MP3 calcula suas fontes ao ser criado: recria no novo tamanho
                s.cd.destroy()
                s.cd = None
            s.retheme()
            theme.refit_areas()
            s.make_room()
        finally:
            s.config(cursor="")

    def change_contrast(s):
        """Liga/desliga o alto contraste (a paleta do tema atual é recalculada)."""
        s.audio.play_click()
        theme.set_contrast(s.high_contrast.get())
        s.save_view_config()
        s.retheme()
        theme.refit_areas()

    def make_room(s):
        """Texto grande deixa o painel da esquerda mais largo: se a pré-visualização ficar apertada,
        alarga a janela (só se a tela permitir e a janela não estiver maximizada nem em tela cheia)."""
        s.update_idletasks()
        if s.attributes("-fullscreen") or s.state() == "zoomed":
            return
        need = theme.px(520) - s.cv.winfo_width()
        if need <= 0:
            return
        sw = s.winfo_screenwidth()
        w = min(s.winfo_width() + need, int(sw * .98))
        x = max(0, min(s.winfo_x(), sw - w))
        s.geometry(f"{w}x{s.winfo_height()}+{x}+{max(0, s.winfo_y())}")

    def toggle_fullscreen(s, e=None):
        """Alterna tela cheia (botão, F11). Esc sai."""
        on = not bool(s.attributes("-fullscreen"))
        s.audio.play_click()
        s.attributes("-fullscreen", on)
        s.fsbtn.config(text="✕ Sair da tela cheia" if on else "⛶ Tela cheia")

    def exit_fullscreen(s, e=None):
        if s.attributes("-fullscreen"):
            s.toggle_fullscreen()

    def fit_window(s):
        """Tamanho da janela proporcional à tela (cabe em notebooks pequenos e usa o espaço de monitores grandes)."""
        sw, sh = s.winfo_screenwidth(), s.winfo_screenheight()
        w = min(max(theme.px(1260), int(sw * .62)), int(sw * .92))
        h = min(max(theme.px(860), int(sh * .72)), int(sh * .88))
        s.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - int(sh * .03))}")
        s.minsize(min(theme.px(900), w), min(theme.px(540), h))

    # ---------- aba "Quantidades" ----------
    def build_tab_qty(s, Q):
        ttk.Label(Q, style="Sec.TLabel", text="Tipos de botton").pack(anchor="w")
        ttk.Label(Q, style="Info.TLabel", wraplength=theme.wrap(270), justify="left",
                  text="Bottons com a mesma arte são agrupados em um tipo. Defina quantos de cada tipo vão para a folha. Se passar de uma página, o programa cria mais páginas automaticamente.").pack(anchor="w")
        tf = ttk.Frame(Q); tf.pack(fill="x", pady=(8, 0))
        ttk.Label(tf, text="Tolerância").pack(side="left")
        w_ = ttk.Scale(tf, from_=8, to=45, variable=s.tol, orient="horizontal")
        w_.pack(side="left", fill="x", expand=True, padx=6)
        ajuda.Tooltip(w_, "Quão parecidos dois bottons precisam ser para virarem o mesmo tipo. Depois de mexer, clique em Reagrupar.")
        w_ = ttk.Button(tf, text="Reagrupar", command=s.regroup_btn)
        w_.pack(side="left")
        ajuda.Tooltip(w_, "Agrupa de novo os bottons parecidos usando a tolerância escolhida.")
        ttk.Label(Q, style="Info.TLabel", text="Maior tolerância = agrupa mais bottons parecidos.").pack(anchor="w")
        w_ = ttk.Button(Q, text="Todos = 1", command=s.all_one)
        w_.pack(side="bottom", fill="x", pady=(6, 0))
        ajuda.Tooltip(w_, "Coloca 1 botton de cada tipo na folha.")
        s.qinfo = ttk.Label(Q, style="Sec.TLabel", text="", wraplength=theme.wrap(270), justify="left")
        s.qinfo.pack(side="bottom", anchor="w", pady=(8, 0))
        box, s.qin = theme.scrolled(Q, s, pad=0, width=theme.wrap(290))
        box.pack(fill="both", expand=True, pady=(8, 0))
        s.build_types()

    def groups(s):
        """{grupo: [índices em s.items]} na ordem em que cada tipo aparece."""
        g = {}
        for n, i in enumerate(s.items):
            g.setdefault(i["grp"], []).append(n)
        return g

    def sheet_items(s):
        """Índices (em s.items) que vão para a folha: o botton-modelo de cada tipo, repetido 'quantidade' vezes."""
        out = []
        for g, ns in s.groups().items():
            out += [ns[0]] * s.qty.get(g, 1)
        return out

    def regroup(s):
        """Agrupa bottons de mesma arte, mesmo quando vieram de folhas diferentes."""
        s.qty = {}
        if not s.sources:
            return
        labels = cluster([s._signature(i) for i in s.items], s.tol.get())
        for it, g in zip(s.items, labels):
            it["grp"] = g
            s.qty[g] = s.qty.get(g, 0) + 1

    def regroup_btn(s):
        sel = s.sel()
        s.regroup()
        s.refresh()
        if sel is not None and sel < len(s.items):
            s.lb.selection_set(sel)

    def assign(s, it):
        """Novo botton: entra no tipo mais parecido, considerando todas as folhas carregadas."""
        sg = s._signature(it)
        best = None
        for g, ns in s.groups().items():
            if g is None:
                continue
            rp = s.items[ns[0]]
            d = distance(sg, s._signature(rp))
            if d < s.tol.get() and (best is None or d < best[0]):
                best = (d, g)
        if best:
            it["grp"] = best[1]
        else:
            it["grp"] = max(s.qty, default=-1) + 1
            s.qty[it["grp"]] = 0
        s.qty[it["grp"]] = s.qty.get(it["grp"], 0) + 1

    def all_one(s):
        for v in s.qvars.values():
            v.set("1")

    def qty_changed(s, g, v):
        try:
            q = max(0, min(999, int(v.get())))
        except (ValueError, tk.TclError):
            return
        if s.qty.get(g) != q:
            s.qty[g] = q
            if s.qjob:
                s.after_cancel(s.qjob)
            s.qjob = s.after(350, lambda: s.refresh(types=False))

    def _source_label(s, idx):
        """Nome curto e único para mostrar as folhas carregadas."""
        if idx < 0 or idx >= len(s.sources):
            return ""
        return s.sources[idx]["label"]

    def _set_active_source(s, idx):
        if not s.sources:
            s.active_source, s.src = 0, None
            s.source_var.set("")
            return
        idx = max(0, min(int(idx), len(s.sources) - 1))
        s.active_source = idx
        s.src = s.sources[idx]["image"]
        s.source_var.set(s.sources[idx]["label"])

    def _refresh_source_selector(s):
        vals = [x["label"] for x in s.sources]
        s.source_cb.configure(values=vals, state="readonly" if vals else "disabled")
        if vals:
            s._set_active_source(s.active_source)
            extra = f"{len(vals)} folhas carregadas." if len(vals) > 1 else "1 folha carregada."
            s.sources_lbl.config(text=extra)
        else:
            s.source_var.set("")
            s.sources_lbl.config(text="Nenhuma folha carregada.")

    def on_source_selected(s, e=None):
        try:
            idx = s.source_cb.current()
        except tk.TclError:
            idx = -1
        if idx >= 0:
            s._set_active_source(idx)
            s.update_selhint("Folha ativa: " + s._source_label(idx))

    def build_types(s):
        for w in s.qin.winfo_children():
            w.destroy()
        s.qvars, s.thumbs = {}, []
        gs = s.groups() if s.sources else {}
        if not gs:
            ttk.Label(s.qin, style="Info.TLabel", text="Selecione uma ou mais folhas para ver os tipos.").pack(anchor="w")
        for g, ns in gs.items():
            it = s.items[ns[0]]
            row = ttk.Frame(s.qin, padding=(0, 4)); row.pack(fill="x")
            # Reaproveita a mesma arte do cache; isso evita uma segunda passagem pesada
            # pelo Pillow/OpenCV apenas para desenhar a miniatura.
            th = s._button(ns[0], 40).resize((theme.px(56),) * 2, Image.BICUBIC)
            ph = ImageTk.PhotoImage(th); s.thumbs.append(ph)
            tk.Label(row, image=ph, bg=theme.PANEL, bd=0).pack(side="left")
            tx = ttk.Frame(row); tx.pack(side="left", fill="x", expand=True, padx=8)
            ttk.Label(tx, text=f"Botton #{ns[0] + 1}", style="Sec.TLabel").pack(anchor="w")
            ttk.Label(tx, style="Info.TLabel",
                      text="único na seleção" if len(ns) == 1 else f"{len(ns)} iguais na seleção").pack(anchor="w")
            v = tk.StringVar(value=str(s.qty.get(g, 1)))
            v.trace_add("write", lambda *a, g=g, v=v: s.qty_changed(g, v))
            ttk.Spinbox(row, from_=0, to=999, width=5, textvariable=v).pack(side="right")
            s.qvars[g] = v

    # ---------- entrada e detecção ----------
    def _choose_images(s, title="Selecionar folhas de bottons"):
        paths = filedialog.askopenfilenames(
            title=title,
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos os arquivos", "*.*")],
        )
        return list(paths or [])

    def _load_source(s, path):
        """Carrega uma folha e devolve (registro, bottons_detectados).
        Folha gigante é reduzida ao abrir (ver process.open_sheet): rec["orig_size"] guarda o tamanho original."""
        s.config(cursor="watch")
        s.update_idletasks()   # mostra o cursor de espera antes do trabalho pesado
        try:
            src, orig_size = open_sheet(path)
            bgr = cv2.cvtColor(np.asarray(src), cv2.COLOR_RGB2BGR)
            circles = detect_circles(bgr)
        finally:
            s.config(cursor="")
        base = os.path.basename(path)
        return {"path": path, "image": src, "name": base, "orig_size": orig_size}, circles

    def _unique_source_label(s, name):
        used = {x["label"] for x in s.sources}
        if name not in used:
            return name
        stem, ext = os.path.splitext(name)
        n = 2
        while f"{stem} ({n}){ext}" in used:
            n += 1
        return f"{stem} ({n}){ext}"

    def _append_source_records(s, paths, replace=False):
        if replace:
            s.sources = []
            s.items = []
            s.qty = {}
            s.active_source = 0
            s._positions_cache_key = None
            s._clear_button_cache()
        added_items = 0
        no_detect = []
        reduced = []   # folhas gigantes que foram reduzidas ao abrir
        start = len(s.sources)
        for path in paths:
            try:
                rec, circles = s._load_source(path)
            except MemoryError:
                log_error(traceback.format_exc())
                messagebox.showwarning("Abrir imagem", f"Memória insuficiente para abrir:\n{os.path.basename(path)}\n\n"
                                       "Feche outros programas ou reduza a imagem (por exemplo, para 10.000 px no lado maior) "
                                       "e tente de novo.", parent=s)
                continue
            except Exception as ex:
                log_error(traceback.format_exc())
                messagebox.showwarning("Abrir imagem", f"Não foi possível abrir:\n{os.path.basename(path)}\n\n{ex}", parent=s)
                continue
            rec["label"] = s._unique_source_label(rec["name"])
            s.sources.append(rec)
            src = rec["image"]
            if rec["orig_size"] != src.size:
                reduced.append((rec["label"], rec["orig_size"], src.size))
            if circles:
                new_items = [s.mk(x, y, r, src=src, source_index=len(s.sources) - 1) for x, y, r in circles]
                if replace:
                    s.items.extend(new_items)
                    added_items += len(new_items)
                else:
                    # Primeiro mantém os tipos/quantidades já ajustados pelo usuário;
                    # os bottons da nova folha entram nos grupos parecidos e aumentam
                    # a quantidade daquele tipo.
                    for it in new_items:
                        s.assign(it)
                        s.items.append(it)
                        added_items += 1
            else:
                no_detect.append(rec["label"])
        if s.sources:
            s._set_active_source(min(s.active_source, len(s.sources) - 1))
        s._refresh_source_selector()
        if replace:
            s.regroup()
        else:
            # Garante grupos consistentes quando só novas folhas sem detecção foram
            # adicionadas ou quando o estado anterior estava vazio.
            if len(s.items) and not any(it.get("grp") is not None for it in s.items):
                s.regroup()
        s.refresh()
        if reduced:
            milhar = lambda v: f"{v:,}".replace(",", ".")   # 27553 -> 27.553 (só nos números, não no nome do arquivo)
            linhas = "\n".join(f"• {n}: {milhar(o[0])} × {milhar(o[1])} px  →  {milhar(t[0])} × {milhar(t[1])} px"
                               for n, o, t in reduced)
            messagebox.showinfo("Folha muito grande", "Para caber na memória, a folha foi reduzida ao abrir:\n\n" + linhas +
                                "\n\nNormalmente isso não muda a qualidade da impressão: um botton de 42 mm a 900 DPI usa "
                                "cerca de 1.500 pixels, e a arte de cada botton normalmente continua com mais do que isso.", parent=s)
        return added_items, no_detect, len(s.sources) - start

    def open(s):
        paths = s._choose_images()
        if not paths:
            return
        added, no_detect, loaded = s._append_source_records(paths, replace=True)
        if not loaded:
            return
        if not s.items:
            messagebox.showinfo("Detecção", "Nenhum botton foi detectado nas folhas selecionadas. Use 'Adicionar' para marcar manualmente.", parent=s)
        elif no_detect:
            messagebox.showinfo("Detecção", "Estas folhas foram carregadas, mas nenhum botton foi detectado nelas:\n\n" + "\n".join(no_detect) + "\n\nVocê pode torná-las ativas na lista de folhas e usar 'Adicionar'.", parent=s)

    def add_sources(s):
        paths = s._choose_images("Adicionar folhas de bottons")
        if not paths:
            return
        added, no_detect, loaded = s._append_source_records(paths, replace=False)
        if loaded and no_detect:
            messagebox.showinfo("Detecção", "Algumas folhas foram adicionadas sem bottons detectados:\n\n" + "\n".join(no_detect), parent=s)
        elif loaded and added:
            s.update_selhint(f"{loaded} folha(s) adicionada(s): {added} botton(s) incorporado(s) à seleção.")

    def clear_sources(s):
        if not s.sources:
            s.update_selhint("Nenhuma folha carregada.")
            return
        if not messagebox.askyesno("Limpar folhas", "Remover todas as folhas e começar uma seleção nova?", parent=s):
            return
        s.sources = []
        s.active_source = 0
        s.src = None
        s.items = []
        s.qty = {}
        s._positions_cache_key = None
        s._clear_button_cache()
        s._refresh_source_selector()
        s.refresh()

    def add(s):
        if not s.src:
            return
        w = tk.Toplevel(s)
        w.title("Arraste do centro para a borda do botton")
        k = min(1.0, s.winfo_screenwidth() * .9 / s.src.width, s.winfo_screenheight() * .8 / s.src.height)
        ph = ImageTk.PhotoImage(s.src.resize((int(s.src.width * k), int(s.src.height * k))))
        c = tk.Canvas(w, width=ph.width(), height=ph.height())
        c.pack()
        c.create_image(0, 0, anchor="nw", image=ph)
        t_ = c.create_text(ph.width() // 2, 8, anchor="n", fill="white", font=(theme.F, theme.fz(10, 1.5), "bold"),
                           width=max(120, ph.width() - 16), justify="center",
                           text="Arraste do CENTRO até a BORDA do botton e solte. (Esc cancela)")
        bar = c.create_rectangle(0, 0, ph.width(), c.bbox(t_)[3] + 8, fill="#222222", outline="")   # a faixa cresce com o texto
        c.tag_lower(bar, t_)
        w.bind("<Escape>", lambda e: w.destroy())
        w.focus_set()
        c.ph, st = ph, {}
        def press(e): st.update(x=e.x, y=e.y, id=c.create_oval(e.x, e.y, e.x, e.y, outline="red", width=2))
        def drag(e):
            r = ((e.x - st["x"]) ** 2 + (e.y - st["y"]) ** 2) ** .5
            c.coords(st["id"], st["x"] - r, st["y"] - r, st["x"] + r, st["y"] + r)
        def rel(e):
            r = ((e.x - st["x"]) ** 2 + (e.y - st["y"]) ** 2) ** .5 / k
            if r > 5:
                x, y = st["x"] / k, st["y"] / k
                s.items.append(s.mk(x, y, r, src=s.src, source_index=s.active_source))
                s.assign(s.items[-1])
                s.refresh()
            w.destroy()
        c.bind("<ButtonPress-1>", press); c.bind("<B1-Motion>", drag); c.bind("<ButtonRelease-1>", rel)

    def mk(s, x, y, r, src=None, source_index=None):
        src = src or s.src
        if source_index is None:
            source_index = s.active_source
        if s.trim.get():
            x, y, r = trim_margin(src, x, y, r)
        return {"cx": x, "cy": y, "r": r, "rot": 0, "color": None,
                "auto": auto_color(src, x, y, r), "grp": None,
                "src": src, "source_index": source_index}

    SEL_HINT = "Clique em um botton da lista — ou diretamente em um botton da folha — para selecionar e ajustar o recorte."

    def update_selhint(s, msg=None):
        s.selhint.config(text=msg or (s.SEL_HINT if s.sources else ""))

    def need_sel(s):
        """Botão de ajuste usado sem botton selecionado: avisa em vez de não fazer nada."""
        s.update_selhint("⚠ Primeiro selecione uma imagem." if not s.sources else "⚠ Primeiro clique em um botton da lista.")
        s.after(3500, s.update_selhint)

    def trim_sel(s):
        i = s.sel()
        if i is None:
            s.need_sel()
        else:
            it = s.items[i]
            src = it["src"]
            it["cx"], it["cy"], it["r"] = trim_margin(src, it["cx"], it["cy"], it["r"])
            it["auto"] = auto_color(src, it["cx"], it["cy"], it["r"])
            s.refresh(); s.lb.selection_set(i)

    # ---------- edição ----------
    def sel(s):
        i = s.lb.curselection()
        return i[0] if i else None

    def remove(s):
        i = s.sel()
        if i is None:
            s.need_sel()
        else:
            it = s.items.pop(i)
            if all(x["grp"] != it["grp"] for x in s.items):
                s.qty.pop(it["grp"], None)   # o tipo deixou de existir
            s.refresh()

    def move(s, d):
        i = s.sel()
        if i is None:
            s.need_sel()
        elif 0 <= i + d < len(s.items):
            s.items[i], s.items[i + d] = s.items[i + d], s.items[i]
            s.refresh(); s.lb.selection_set(i + d)

    def adj(s, k, d):
        i = s.sel()
        if i is None:
            s.need_sel()
            return
        it = s.items[i]
        it[k] += d if k == "rot" else d * it["r"] * .02

        # Durante o ajuste manual não reconstruímos a lista inteira, as miniaturas e todas as páginas a
        # cada clique. A prévia continua em PREVIEW_DPI (120): só o botton ajustado é refeito, o resto vem do
        # cache; as miniaturas só são refeitas 250 ms depois que o usuário para de ajustar.
        src_label = s._source_label(it.get("source_index", -1))
        suffix = f"  · {src_label}" if len(s.sources) > 1 and src_label else ""
        s.lb.delete(i)
        s.lb.insert(i, f"#{i + 1}  r={it['r']:.0f}px  cor={'manual' if it['color'] else 'auto'}{suffix}")
        s.lb.selection_set(i)
        s._refresh_adjustment(i)

    def pick(s):
        i = s.sel()
        if i is None:
            s.need_sel()
            return
        c = colorchooser.askcolor()[0]
        if c:
            s.items[i]["color"] = tuple(int(v) for v in c)
            s.refresh()
            s.lb.selection_set(i)

    def _top_colors(s, it, limit=5):
        """Extrai as cores mais representativas do botton selecionado.

        A amostra é limitada ao círculo do próprio botton para não puxar a cor
        branca/cinza da folha ao redor. As cores são agrupadas por proximidade
        para evitar cinco tons quase iguais e ordenadas pela quantidade de pixels.
        """
        src = it.get("src") or s.src
        if src is None:
            return []
        try:
            cx, cy, r = float(it["cx"]), float(it["cy"]), float(it["r"])
            left = max(0, int(cx - r))
            top = max(0, int(cy - r))
            right = min(src.width, int(cx + r + 1))
            bottom = min(src.height, int(cy + r + 1))
            if right <= left or bottom <= top:
                return []

            # Trabalha em uma amostra pequena: suficiente para cores e bem mais rápido
            # que analisar todos os pixels de uma foto grande.
            crop = src.convert("RGB").crop((left, top, right, bottom))
            max_side = 180
            if max(crop.size) > max_side:
                scale = max_side / max(crop.size)
                crop = crop.resize((max(1, int(crop.width * scale)), max(1, int(crop.height * scale))), Image.Resampling.BILINEAR)

            arr = np.asarray(crop, dtype=np.int16)
            h, w = arr.shape[:2]
            yy, xx = np.ogrid[:h, :w]
            # Pequena margem de segurança para não pegar o papel fora do contorno.
            rr = min(w, h) / 2.0 * 0.98
            mx = w / 2.0
            my = h / 2.0
            mask = (xx - mx) ** 2 + (yy - my) ** 2 <= rr ** 2
            pix = arr[mask]
            if len(pix) == 0:
                return []

            # Histograma quantizado em 16 níveis/canal: barato e evita que pequenas
            # variações de compressão gerem dezenas de cores quase idênticas.
            bins = np.clip((pix // 16), 0, 15)
            keys = bins[:, 0] * 256 + bins[:, 1] * 16 + bins[:, 2]
            uniq, counts = np.unique(keys, return_counts=True)
            order = np.argsort(counts)[::-1]

            chosen = []
            min_dist2 = 34 ** 2
            for pos in order:
                key = int(uniq[pos])
                b = key // 256
                g = (key // 16) % 16
                rch = key % 16
                # Centro do bin.
                c = np.array([b * 16 + 8, g * 16 + 8, rch * 16 + 8], dtype=np.float32)
                # Rejeita cores muito parecidas com uma já escolhida.
                if any(float(np.sum((c - np.array(prev, dtype=np.float32)) ** 2)) < min_dist2 for prev, _ in chosen):
                    continue
                chosen.append((tuple(int(max(0, min(255, v))) for v in c), int(counts[pos])))
                if len(chosen) >= limit:
                    break

            # A lista acima já está por frequência, mas ignora cores quase invisíveis
            # quando há opções realmente presentes em quantidade relevante.
            return [c for c, _ in chosen]
        except Exception:
            return []

    def palette_picker(s):
        """Mostra cinco cores principais do botton selecionado em um seletor rápido."""
        i = s.sel()
        if i is None:
            s.need_sel()
            return
        colors = s._top_colors(s.items[i], 5)
        if not colors:
            messagebox.showinfo("Cores do botton", "Não foi possível encontrar cores suficientes neste botton.", parent=s)
            return

        w = tk.Toplevel(s)
        w.title("🎲 Cores principais")
        w.transient(s)
        w.resizable(False, False)
        try:
            w.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(w, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Escolha uma cor para o contorno", style="Sec.TLabel").pack(anchor="w")
        ttk.Label(frame, text="As 5 cores mais presentes no botton selecionado", style="Info.TLabel").pack(anchor="w", pady=(2, 10))

        row = ttk.Frame(frame)
        row.pack()

        def choose(rgb):
            s.items[i]["color"] = tuple(rgb)
            w.destroy()
            s.refresh()
            if i < len(s.items):
                s.lb.selection_set(i)
                s.lb.see(i)
                s.update_selhint(f"Cor do contorno definida para #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}.")

        for rgb in colors:
            hx = "#%02X%02X%02X" % rgb
            cell = tk.Frame(row, width=58, height=68, bd=1, relief="solid", bg=hx, cursor="hand2")
            cell.pack(side="left", padx=4)
            cell.pack_propagate(False)
            tk.Label(cell, text="", bg=hx, bd=0).pack(fill="both", expand=True)
            tk.Label(cell, text=hx, bg=hx, fg="#FFFFFF" if sum(rgb) < 390 else "#111111", font=(theme.F, 8, "bold"), bd=0).pack(fill="x")
            cell.bind("<Button-1>", lambda e, c=rgb: choose(c))
            for child in cell.winfo_children():
                child.bind("<Button-1>", lambda e, c=rgb: choose(c))

        ttk.Button(frame, text="Cancelar", command=w.destroy).pack(anchor="e", pady=(10, 0))
        w.bind("<Escape>", lambda e: w.destroy())
        w.update_idletasks()
        sw, sh = s.winfo_screenwidth(), s.winfo_screenheight()
        ww, wh = w.winfo_width(), w.winfo_height()
        w.geometry(f"{ww}x{wh}+{max(10, (sw - ww)//2)}+{max(10, (sh - wh)//2)}")

    def eyedropper(s):
        """Conta-gotas visual para escolher a cor do contorno diretamente da imagem.

        A janela usa um layout estável: o painel de informações não muda de largura
        a cada movimento do mouse, evitando o "tremelicar" causado por realinhamento
        do cabeçalho. A amostra RGB/HEX é lida da imagem original.
        """
        i = s.sel()
        if i is None:
            s.need_sel()
            return

        it = s.items[i]
        src = it.get("src") or s.src
        if src is None:
            s.need_sel()
            return

        w = tk.Toplevel(s)
        w.title("Conta-gotas · escolher cor")
        w.transient(s)
        w.resizable(False, False)

        max_w = min(1100, max(620, s.winfo_screenwidth() - 180))
        max_h = min(760, max(480, s.winfo_screenheight() - 180))
        scale = min(max_w / src.width, max_h / src.height, 1.0)
        dw = max(1, int(round(src.width * scale)))
        dh = max(1, int(round(src.height * scale)))
        preview = src.resize((dw, dh), Image.LANCZOS) if scale < 1.0 else src
        ph = ImageTk.PhotoImage(preview)

        # Tamanho final centrado na tela.
        outer_w = min(max_w + 36, dw + 36)
        outer_h = min(max_h + 165, dh + 165)
        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()
        gx = max(10, (sw - outer_w) // 2)
        gy = max(10, (sh - outer_h) // 2)
        w.geometry(f"{outer_w}x{outer_h}+{gx}+{gy}")
        w.minsize(outer_w, outer_h)

        try:
            w.grab_set()
        except tk.TclError:
            pass

        # ---------- cabeçalho ----------
        head = ttk.Frame(w, padding=(14, 12, 14, 8))
        head.pack(fill="x")

        title_row = ttk.Frame(head)
        title_row.pack(fill="x")
        ttk.Label(title_row, text="Conta-gotas", style="Sec.TLabel",
                  font=(theme.F, theme.fz(14), "bold")).pack(side="left")
        ttk.Label(title_row, text="ESC cancela  ·  clique para selecionar",
                  style="Info.TLabel").pack(side="right")

        ttk.Label(
            head,
            text="Mova o cursor sobre a imagem para visualizar a cor. O contorno será atualizado quando você clicar.",
            style="Info.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        # ---------- área da imagem ----------
        body = ttk.Frame(w, padding=(14, 0, 14, 10))
        body.pack(fill="both", expand=True)

        frame = tk.Frame(body, bd=1, relief="solid", highlightthickness=0)
        frame.pack()

        cv = tk.Canvas(
            frame,
            width=dw,
            height=dh,
            highlightthickness=0,
            bd=0,
            cursor="crosshair",
        )
        cv.pack()
        cv.create_image(0, 0, anchor="nw", image=ph)
        cv.image_ref = ph

        # Cursor visual: círculo + pequenas linhas, sem redesenhar o Canvas inteiro.
        cursor_items = {
            "ring": cv.create_oval(-8, -8, 8, 8, outline="#FFFFFF", width=2),
            "ring2": cv.create_oval(-10, -10, 10, 10, outline="#111111", width=1),
            "h1": cv.create_line(-16, 0, -9, 0, fill="#FFFFFF", width=1),
            "h2": cv.create_line(9, 0, 16, 0, fill="#FFFFFF", width=1),
            "v1": cv.create_line(0, -16, 0, -9, fill="#FFFFFF", width=1),
            "v2": cv.create_line(0, 9, 0, 16, fill="#FFFFFF", width=1),
        }

        # ---------- painel de informações fixo ----------
        panel = ttk.Frame(w, padding=(14, 0, 14, 10))
        panel.pack(fill="x")

        swatch_box = tk.Frame(panel, width=56, height=44, bd=0, highlightthickness=0)
        swatch_box.pack(side="left", padx=(0, 10))
        swatch_box.pack_propagate(False)

        swatch = tk.Label(
            swatch_box,
            text="",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
        )
        swatch.pack(fill="both", expand=True)

        data = ttk.Frame(panel)
        data.pack(side="left", fill="x", expand=True)

        hex_var = tk.StringVar(value="HEX  #FFFFFF")
        rgb_var = tk.StringVar(value="RGB  (255, 255, 255)")
        pos_var = tk.StringVar(value="POSIÇÃO  0 × 0")

        ttk.Label(data, textvariable=hex_var, style="Sec.TLabel",
                  font=(theme.F, theme.fz(11), "bold")).pack(anchor="w")
        ttk.Label(data, textvariable=rgb_var, style="Info.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Label(data, textvariable=pos_var, style="Info.TLabel").pack(anchor="w", pady=(2, 0))

        ttk.Button(panel, text="Cancelar", width=11, command=lambda: cancel_grab()).pack(side="right")

        # Linha inferior fixa: não muda de tamanho enquanto o cursor passa pelas cores.
        ttk.Separator(w).pack(fill="x")
        foot = ttk.Frame(w, padding=(14, 8))
        foot.pack(fill="x")
        ttk.Label(
            foot,
            text="Amostra precisa da imagem original  ·  Clique para aplicar a cor ao aro de 5 mm",
            style="Info.TLabel",
        ).pack(side="left")
        ttk.Label(
            foot,
            text="Botão direito / Esc: cancelar",
            style="Info.TLabel",
        ).pack(side="right")

        state = {"last_xy": None, "last_rgb": None}

        def move_cursor(x, y):
            cv.coords(cursor_items["ring"], x - 8, y - 8, x + 8, y + 8)
            cv.coords(cursor_items["ring2"], x - 10, y - 10, x + 10, y + 10)
            cv.coords(cursor_items["h1"], x - 16, y, x - 9, y)
            cv.coords(cursor_items["h2"], x + 9, y, x + 16, y)
            cv.coords(cursor_items["v1"], x, y - 16, x, y - 9)
            cv.coords(cursor_items["v2"], x, y + 9, x, y + 16)

        def sample(e, commit=False):
            x = max(0, min(dw - 1, int(e.x)))
            y = max(0, min(dh - 1, int(e.y)))

            # Converte o ponto da prévia para a imagem original.
            ox = min(src.width - 1, max(0, int(round(x / max(scale, 1e-9)))))
            oy = min(src.height - 1, max(0, int(round(y / max(scale, 1e-9)))))
            rgb = tuple(int(v) for v in src.getpixel((ox, oy))[:3])

            # Move o cursor sempre; atualiza os textos apenas quando a amostra mudou.
            move_cursor(x, y)

            if state["last_xy"] == (ox, oy) and state["last_rgb"] == rgb and not commit:
                return

            state["last_xy"] = (ox, oy)
            state["last_rgb"] = rgb

            hx = "#%02X%02X%02X" % rgb
            swatch.configure(bg=hx)
            hex_var.set(f"HEX  {hx}")
            rgb_var.set(f"RGB  ({rgb[0]}, {rgb[1]}, {rgb[2]})")
            pos_var.set(f"POSIÇÃO  {ox} × {oy}")

            if commit:
                it["color"] = rgb
                cancel_grab()
                s._refresh_adjustment(i)
                s.lb.selection_set(i)

        def cancel_grab(e=None):
            try:
                w.grab_release()
            except tk.TclError:
                pass
            try:
                w.destroy()
            except tk.TclError:
                pass
            return "break"

        cv.bind("<Motion>", sample)
        cv.bind("<Button-1>", lambda e: sample(e, True))
        cv.bind("<Button-3>", cancel_grab)
        w.bind("<Escape>", cancel_grab)
        w.bind("<Return>", cancel_grab)
        w.protocol("WM_DELETE_WINDOW", cancel_grab)

        try:
            cv.focus_set()
        except tk.TclError:
            pass

    def reset_color(s):
        i = s.sel()
        if i is None:
            s.need_sel()
        else:
            s.items[i]["color"] = None; s.refresh(); s.lb.selection_set(i)

    def _invalidate_view(s):
        """Descarta apenas o bitmap visível; os bottons renderizados continuam no cache."""
        if s._view_job:
            try:
                s.after_cancel(s._view_job)
            except tk.TclError:
                pass
            s._view_job = None
        if s._settle_job:
            try:
                s.after_cancel(s._settle_job)
            except tk.TclError:
                pass
            s._settle_job = None
        s._view_key = None
        s._view_force_key = None
        if s.cv.winfo_exists():
            s.cv.delete("view")
        s._view_item = None

    def _clear_button_cache(s):
        s._button_cache.clear()
        s._signature_cache.clear()
        s._invalidate_view()

    def on_combo(s, e=None):
        s.audio.play_click()
        if s.bg.get() == "personalizado":
            c = colorchooser.askcolor()[1]
            s.bgcolor = c or s.bgcolor
        s.refresh()

    # ---------- renderização ----------
    def num(s, v, d):
        try:
            return float(v.get().replace(",", "."))
        except ValueError:
            return d

    def gapmm(s):
        """Espaçamento em mm (nunca negativo)."""
        return max(0.0, s.num(s.gap, 3))

    def sheet_size(s):
        return (s.num(s.cw, 210), s.num(s.ch, 297)) if s.sheet.get() == "Personalizado" else SHEETS[s.sheet.get()]

    def update_fit(s):
        """Diz quantas colunas/linhas cabem por página e sugere como encaixar mais."""
        W, H = s.sheet_size()
        total, gap, al = s.size.get() + 10, s.gapmm(), s.align.get()
        c, r = grid_size(total, gap, W, H, al)
        if total > W or total > H:
            s.fit.config(text="⚠ O botton (com o contorno) é maior que a folha.")
            s.fit_tip.config(text="")
            return
        s.fit.config(text=f"Em cada folha cabem {c} coluna(s) × {r} linha(s) = {c * r} bottons.")
        cands = []
        if gap > 0:
            cands.append((0, al, "espaçamento 0"))
        if al == "center":
            cands.append((gap, "topleft", "a posição “Canto superior”"))
        if gap > 0 and al == "center":
            cands.append((0, "topleft", "espaçamento 0 e a posição “Canto superior”"))
        best = None
        for g, a, how in cands:
            cc, rr = grid_size(total, g, W, H, a)
            if cc * rr > c * r and (best is None or cc * rr > best[0]):
                best = (cc * rr, cc, rr, how)
        s.fit_tip.config(text=f"Dica: com {best[3]} cabem {best[1]} × {best[2]} = {best[0]} por folha." if best else "")

    def update_step(s):
        """Texto-guia: diz qual é o próximo passo."""
        if not s.sources:
            t_ = "Passo 1: clique em “Selecionar imagem”. Você pode escolher várias folhas ou acrescentar outras depois."
        elif not s.items:
            t_ = "Nenhum botton detectado: use “Adicionar” e arraste do centro até a borda de cada botton."
        elif not s.sheet_items():
            t_ = "Nenhum botton na folha: aumente a quantidade na aba “Quantidades”."
        else:
            t_ = (f"Passo 2: confira os {len(s.items)} botton(s) detectado(s). Passo 3: defina as quantidades na aba "
                  "“Quantidades”. Passo 4: Exportar ou Imprimir.")
        s.step_lbl.config(text=t_)

    def key_nav(s, d):
        if s.prevs:
            s.nav(d)

    def check_sheet(s, title):
        """Avisa por que não dá para exportar/imprimir (antes o botão simplesmente não fazia nada)."""
        if not s.sources:
            messagebox.showinfo(title, "Primeiro selecione uma ou mais folhas com os seus bottons (botão “Selecionar imagem”).")
            return False
        if not s.sheet_items():
            messagebox.showinfo(title, "Não há bottons na folha. Aumente a quantidade na aba “Quantidades”.")
            return False
        return True

    def maybe_intro(s):
        if not load_cfg().get("intro_vista"):
            s.show_intro()

    def show_intro(s):
        ajuda.Intro(s, s.intro_done)

    def intro_done(s):
        cfg = load_cfg()
        cfg["intro_vista"] = True
        save_cfg(cfg)

    def bgrgba(s):
        m = s.bg.get()
        if m == "transparente":
            return (255, 255, 255, 0)
        if m == "personalizado":
            h = s.bgcolor.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        return (255, 255, 255, 255)

    def _signature(s, it):
        """Assinatura pequena da arte, cacheada enquanto a geometria do item não muda."""
        key = (id(it["src"]), round(it["cx"], 3), round(it["cy"], 3), round(it["r"], 3))
        sig = s._signature_cache.get(key)
        if sig is None:
            sig = signature(it["src"], it["cx"], it["cy"], it["r"])
            if len(s._signature_cache) >= 512:
                s._signature_cache.pop(next(iter(s._signature_cache)))
            s._signature_cache[key] = sig
        return sig

    def _button_key(s, n, dpi):
        i = s.items[n]
        color = tuple(i["color"] or i["auto"])
        return (id(i["src"]), round(i["cx"], 3), round(i["cy"], 3), round(i["r"], 3),
                round(i["rot"], 2), s.size.get(), int(dpi), color)

    def _button(s, n, dpi):
        """Renderiza um botton uma única vez por configuração e reaproveita a imagem depois.
        Isso evita repetir OpenCV/Pillow a cada toque nas setas de ajuste.
        """
        key = s._button_key(n, dpi)
        b = s._button_cache.get(key)
        if b is None:
            i = s.items[n]
            b = make_button(i["src"], i["cx"], i["cy"], i["r"], s.size.get(), dpi,
                             i["color"] or i["auto"], i["rot"])
            if len(s._button_cache) >= 320:
                s._button_cache.pop(next(iter(s._button_cache)))
            s._button_cache[key] = b
        return b

    def _schedule_adjust_types(s):
        """Adia a reconstrução das miniaturas para não travar durante cliques rápidos de ajuste."""
        if s._adjust_type_job:
            try:
                s.after_cancel(s._adjust_type_job)
            except tk.TclError:
                pass
        s._adjust_type_job = s.after(250, s._finish_adjust_types)

    def _finish_adjust_types(s):
        s._adjust_type_job = None
        if s.sources:
            s.build_types()

    def _refresh_adjustment(s, i):
        """Atualiza somente a página atual (a mesma prévia de 120 DPI do resto do programa) durante o ajuste manual.
        Não reconstrói todas as páginas: só o botton ajustado é refeito, os outros vêm do cache."""
        s.ver += 1
        s.hi = None
        if s.hijob:
            try:
                s.after_cancel(s.hijob)
            except tk.TclError:
                pass
            s.hijob = None
        if s.sources and s.prevs:
            # O número/layout das páginas não mudou; só a arte de um botton foi alterada.
            s.prevs[s.page] = s._page_preview(s.page, PREVIEW_DPI)
            s.prev = s.prevs[s.page]
        else:
            s.prevs = s.pages(PREVIEW_DPI) if s.sources else []
            s.prev = s.prevs[s.page] if s.prevs else None
        s._invalidate_view()
        s.show()
        s._schedule_adjust_types()

    def _layout_data(s):
        """Dados geométricos da folha, calculados uma vez por configuração."""
        art = s.size.get()
        W, H = (s.num(s.cw, 210), s.num(s.ch, 297)) if s.sheet.get() == "Personalizado" else SHEETS[s.sheet.get()]
        gap = s.gapmm()
        return W, H, art + 10, gap

    def _positions_cached(s, count):
        key = (count, *s._layout_data(), s.align.get())
        if getattr(s, "_positions_cache_key", None) != key:
            W, H, total, gap = s._layout_data()
            s._positions_cache_key = key
            s._positions_cache = positions(count, total, gap, W, H, s.align.get())
        return s._positions_cache

    def _page_preview(s, pi, dpi):
        """Renderiza somente uma página na resolução pedida."""
        idx = s.sheet_items()
        if not idx:
            return None
        W, H, total, gap = s._layout_data()
        pg = s._positions_cached(len(idx))
        page = Image.new("RGBA", (mm(W, dpi), mm(H, dpi)), s.bgrgba())
        cache = {}
        for i, x, y in pg[min(pi, len(pg) - 1)]:
            n = idx[i]
            if n not in cache:
                cache[n] = s._button(n, dpi)
            page.alpha_composite(cache[n], (mm(x, dpi), mm(y, dpi)))
        return page

    def pages(s, dpi):
        idx = s.sheet_items()
        if not idx:
            return []
        W, H, total, gap = s._layout_data()
        pg = s._positions_cached(len(idx))
        cache, b = {}, []
        for n in idx:
            if n not in cache:
                cache[n] = s._button(n, dpi)
            b.append(cache[n])
        s.geom = (W, H, total, gap)
        return build_pages(b, total, gap, W, H, dpi, s.bgrgba(), s.align.get())

    def refresh(s, types=True):
        sel = s.sel()
        s.lb.delete(0, "end")
        for n, i in enumerate(s.items, 1):
            src_label = s._source_label(i.get("source_index", -1))
            suffix = f"  · {src_label}" if len(s.sources) > 1 and src_label else ""
            s.lb.insert("end", f"#{n}  r={i['r']:.0f}px  cor={'manual' if i['color'] else 'auto'}{suffix}")
        if sel is not None and sel < len(s.items):
            s.lb.selection_set(sel)
        s.ver += 1; s.hi = None
        s._positions_cache_key = None
        if types:
            s.build_types()
        s.prevs = s.pages(PREVIEW_DPI) if s.sources else []
        s.page = max(0, min(s.page, len(s.prevs) - 1))
        s.qinfo.config(text=f"Total na folha: {len(s.sheet_items())} botton(s) · {len(s.prevs)} página(s)" if s.sources else "")
        s.update_fit()
        s.update_step()
        s.update_selhint()
        s._invalidate_view()
        s.nav(0)
        # Uma nova geração das páginas representa um novo aviso: se houver bottons
        # na página seguinte, a seta começa a piscar novamente.
        s._start_next_blink()

    def toggle_nums(s):
        s.shownum = not s.shownum
        s.numbtn.config(text="Ocultar numeração (#)" if s.shownum else "Mostrar numeração (#)")
        s.show()

    def _stop_next_blink(s, dismissed=False):
        """Encerra o alerta da próxima página e devolve a seta ao estilo normal."""
        if s._next_blink_job is not None:
            try:
                s.after_cancel(s._next_blink_job)
            except Exception:
                pass
            s._next_blink_job = None
        s._next_blink_on = False
        if dismissed:
            s._next_blink_dismissed = True
        for b in (getattr(s, "nbn", None), getattr(s, "pg_next", None)):
            if b is not None:
                try:
                    b.configure(style="Mini.TButton")
                except Exception:
                    pass

    def _blink_next_page(s):
        """Pisca as duas setas de avanço sem bloquear a interface."""
        if s._next_blink_dismissed or len(s.prevs) <= s.page + 1:
            s._stop_next_blink()
            return
        s._next_blink_on = not s._next_blink_on
        style = "NextAlert.TButton" if s._next_blink_on else "Mini.TButton"
        for b in (getattr(s, "nbn", None), getattr(s, "pg_next", None)):
            if b is not None:
                try:
                    b.configure(style=style)
                except Exception:
                    pass
        s._next_blink_job = s.after(450, s._blink_next_page)

    def _start_next_blink(s):
        """Inicia o alerta quando existem páginas seguintes e ele ainda não foi visto."""
        s._stop_next_blink()
        s._next_blink_dismissed = False
        if len(s.prevs) > s.page + 1:
            s._blink_next_page()

    def nav(s, d):
        # Qualquer clique/atalho de avanço confirma que o usuário viu o aviso.
        if d > 0:
            s._stop_next_blink(dismissed=True)
        s.page = max(0, min(s.page + d, len(s.prevs) - 1))
        if d:
            s.px = s.py = 0.0
        s.prev = s.prevs[s.page] if s.prevs else None
        n, tot = len(s.prevs), len(s.sheet_items())
        if n > 1:
            info = f"⚠ {tot} bottons não cabem em uma folha: foram divididos em {n} páginas. Você está na página {s.page + 1}."
        elif n == 1:
            info = f"1 página: todos os {tot} bottons cabem na folha."
        else:
            info = ""
        s.info.config(text=info, style="Sec.TLabel" if n > 1 else "Info.TLabel")
        if n:
            s.pg_lbl.config(text=f"Página {s.page + 1} de {n}")
        else:
            s.pg_lbl.config(text="Sem folha")
        for b in (s.nbp, s.pg_prev):
            b.state(["!disabled" if s.page > 0 else "disabled"])
        for b in (s.nbn, s.pg_next):
            b.state(["!disabled" if s.page < n - 1 else "disabled"])
        s.show()

    # ---------- zoom / pan ----------
    def page_image(s, pi, dpi):
        """Compatibilidade: renderiza apenas a página atual na resolução pedida."""
        return s._page_preview(pi, dpi)

    def _render_view_tile(s, immediate_hi=False, fast=False):
        """Renderiza uma área um pouco maior que a janela, em vez de redimensionar a cada evento.
        Durante o pan o Canvas apenas move esse bitmap, o que deixa o arraste muito mais leve.
        fast=True: reamostragem rápida, usada enquanto o zoom/rolagem acontecem (a de qualidade vem logo depois)."""
        if s._view_job:   # chamado direto: cancela o pedido da fila (um render rápido não pode sobrescrever este)
            try:
                s.after_cancel(s._view_job)
            except tk.TclError:
                pass
        s._view_job = None
        if not s.prev:
            s._invalidate_view()
            s.show()
            return

        cw, ch = max(s.cv.winfo_width(), 50), max(s.cv.winfo_height(), 50)
        pw, ph = s.prev.size
        W = s.geom[0] if s.geom else 210
        sc = min((cw - 10) / pw, (ch - 10) / ph) * s.zoom
        dw, dh = pw * sc, ph * sc
        lim_x, lim_y = max(0, (dw - cw) / 2 + 40), max(0, (dh - ch) / 2 + 40)
        px, py = max(-lim_x, min(lim_x, s.px)), max(-lim_y, min(lim_y, s.py))
        if not fast:   # durante o zoom a posição "ideal" é guardada (o ponto sob o cursor fica parado); só no fim ela é presa aos limites
            s.px, s.py = px, py
        left = cw / 2 + px - dw / 2
        top = ch / 2 + py - dh / 2
        # Mantém a transformação usada no desenho para que um clique possa voltar
        # exatamente às coordenadas da folha, inclusive com zoom/pan.
        s._view_transform = (s.page, s.ver, left, top, dw / W)

        src = s.prev
        if s.zoom > 1.0:
            need = dw / W * 25.4
            if immediate_hi or need > 90:
                if s.hi and s.hi[0][:2] == (s.page, s.ver):
                    src = s.hi[1]
                elif immediate_hi:
                    # Não bloqueia a interação criando uma página de 300 DPI agora.
                    # O hi-res será agendado por sched_hi depois da pausa.
                    pass
            if need > 110:   # só quando a prévia de 120 DPI ficaria esticada na tela (antes, a partir de 70: travava à toa)
                s.sched_hi(150 if need <= 170 else 300)

        sw, sh = src.size
        k2 = dw / sw
        buf = int(max(120, min(280, min(cw, ch) * 0.32)))
        tile_w, tile_h = cw + 2 * buf, ch + 2 * buf
        crop_left, crop_top = -buf, -buf
        crop_right, crop_bottom = cw + buf, ch + buf

        bx0 = max(0, int((crop_left - left) / k2))
        by0 = max(0, int((crop_top - top) / k2))
        bx1 = min(sw, int((crop_right - left) / k2) + 2)
        by1 = min(sh, int((crop_bottom - top) / k2) + 2)

        # Canvas não desenha pixels fora da folha; o tile recebe apenas a parte visível da página.
        bgmode = s.bg.get()
        # Fora da folha o tile é transparente para preservar o fundo/degradê do preview.
        tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
        if bx1 > bx0 and by1 > by0:
            part = src.crop((bx0, by0, bx1, by1))
            tx = max(1, round((bx1 - bx0) * k2))
            ty = max(1, round((by1 - by0) * k2))
            part = part.resize((tx, ty), Image.BILINEAR if fast else (Image.LANCZOS if s.zoom <= 1.05 else Image.BICUBIC))
            if bgmode == "transparente":
                base = Image.new("RGB", part.size, (255, 255, 255))
                base.paste(part, mask=part.getchannel("A"))
                part = base.convert("RGBA")
            dx = round(left + bx0 * k2 - crop_left)
            dy = round(top + by0 * k2 - crop_top)
            tile.alpha_composite(part, (dx, dy))

        s.cv.delete("all")
        theme.paint_stage(s.cv)
        s.cv.create_rectangle(left + 6, top + 8, left + dw + 6, top + dh + 8,
                              fill=theme.SHADOW, outline="", tags="view")
        s._view_photo = ImageTk.PhotoImage(tile)
        s._view_item = s.cv.create_image(crop_left, crop_top, anchor="nw",
                                         image=s._view_photo, tags="view")
        s._view_tile_origin = (crop_left, crop_top)
        s._view_buffer = buf
        s._view_key = (s.page, s.ver, round(s.zoom, 4), cw, ch, id(src), bool(s.shownum), bgmode)
        s._view_zoom = s.zoom
        s._view_size = (cw, ch)
        s._tile_pan = (px, py)

        if s.shownum and s.geom:
            Wmm, Hmm, total, gap = s.geom
            k = dw / Wmm
            idx = s.sheet_items()
            pg = s._positions_cached(len(idx))
            for ii, x, y in pg[min(s.page, len(pg) - 1)]:
                bx = left + (x + total / 2) * k
                by = top + (y + total / 2) * k
                rad = total * k * 0.28
                s.cv.create_oval(bx - rad, by - rad, bx + rad, by + rad, fill=theme.NUM,
                                 outline="white", width=2, tags="view")
                s.cv.create_text(bx, by, text=f"#{idx[ii] + 1}", fill=theme.NUM_FG,
                                 font=(theme.F, max(7, int(rad * 0.8)), "bold"), tags="view")

        s.cv.config(cursor="fleur" if s.zoom > 1 else "")

    def schedule_view_render(s, delay=45):
        if s._view_job:
            try:
                s.after_cancel(s._view_job)
            except tk.TclError:
                pass
        try:
            s._view_job = s.after(max(0, int(delay)), s._render_view_tile)
        except tk.TclError:
            s._view_job = None

    def sched_hi(s, dpi):
        if s.hi and s.hi[0][:2] == (s.page, s.ver) and s.hi[0][2] >= dpi:
            return
        if s.hijob:
            try:
                s.after_cancel(s.hijob)
            except tk.TclError:
                pass
        key = (s.page, s.ver, dpi)
        s.hijob = s.after(420, lambda: s.render_hi(key))

    def render_hi(s, key):
        s.hijob = None
        if s.sources and s.prevs and key[:2] == (s.page, s.ver):
            if s.drag:
                s.hijob = s.after(180, lambda: s.render_hi(key))
                return
            s.hi = (key, s._page_preview(key[0], key[2]))
            if s.zoom > 1:
                s.schedule_view_render(0)

    def queue_render(s, fast=True, now=False):
        """Pede um novo desenho da folha SEM apagar o atual: o desenho antigo fica na tela até o novo estar pronto.
        (Antes, cada passo do zoom apagava a folha e cancelava o desenho pendente: ela só voltava depois que a roda
        parava, e era isso que a fazia "sumir".) Pedidos seguidos viram um render só, a cada ~12 ms; depois que o
        movimento para, vem um render de qualidade total."""
        if now and s._view_job:
            try:
                s.after_cancel(s._view_job)
            except tk.TclError:
                pass
            s._view_job = None
        if s._view_job is None:
            try:
                s._view_job = s.after(0 if now else 12, lambda: s._render_view_tile(fast=fast))
            except tk.TclError:
                s._view_job = None
        if fast:
            if s._settle_job:
                try:
                    s.after_cancel(s._settle_job)
                except tk.TclError:
                    pass
            try:
                s._settle_job = s.after(170, s._settle_render)
            except tk.TclError:
                s._settle_job = None

    def _settle_render(s):
        """O zoom/rolagem parou: refaz o desenho com a qualidade total."""
        s._settle_job = None
        if s.drag:   # ainda arrastando: espera
            s._settle_job = s.after(170, s._settle_render)
            return
        s._render_view_tile()

    def _pan_limits(s):
        """Quanto a folha pode se afastar do centro (px, horizontal e vertical) com o zoom atual."""
        cw, ch = max(s.cv.winfo_width(), 50), max(s.cv.winfo_height(), 50)
        pw, ph = s.prev.size
        sc = min((cw - 10) / pw, (ch - 10) / ph) * s.zoom
        return max(0, (pw * sc - cw) / 2 + 40), max(0, (ph * sc - ch) / 2 + 40)

    def _set_zoom_text(s, txt):
        s.zlbl.config(text=txt)
        s.zbtn.config(text=txt)

    def layout_pgbar(s, e=None):
        """Barra de página/zoom: uma linha quando cabe. Com texto grande e janela estreita, o zoom e a tela cheia descem
        para uma segunda linha (nada é cortado e nada cobre a folha)."""
        try:
            w = s.pgbar.winfo_width()
            need = s.pg_nav.winfo_reqwidth() + s.pg_tools.winfo_reqwidth() + theme.px(24)
        except tk.TclError:
            return
        two = 1 < w < need
        if two == getattr(s, "_pgbar_two", None):
            return
        s._pgbar_two = two
        if two:
            s.pg_tools.grid_configure(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        else:
            s.pg_tools.grid_configure(row=0, column=1, columnspan=1, sticky="e", pady=0)

    def zoom_at(s, fac, x, y, immediate=False):
        """Zoom ancorado no ponto (x, y) da folha: o que está sob o cursor fica parado (como no Affinity)."""
        if not s.prev:
            return
        new = max(1.0, min(10.0, s.zoom * fac))
        fac = new / s.zoom
        if abs(fac - 1.0) < 1e-9:
            return
        cw, ch = s.cv.winfo_width(), s.cv.winfo_height()
        s.px = (x - cw / 2) - (x - cw / 2 - s.px) * fac
        s.py = (y - ch / 2) - (y - ch / 2 - s.py) * fac
        s.zoom = new
        if new == 1.0:
            s.px = s.py = 0.0
        s._set_zoom_text(f"{new * 100:.0f}%")
        s._view_key = None   # o desenho atual ficou velho, mas continua na tela até o novo estar pronto (a folha nunca some)
        s.queue_render(fast=True, now=immediate)

    def zoom_btn(s, fac):
        s.zoom_at(fac, s.cv.winfo_width() / 2, s.cv.winfo_height() / 2, immediate=True)

    def zoom_reset(s):
        s.zoom, s.px, s.py = 1.0, 0.0, 0.0
        s._set_zoom_text("100%")
        s._view_key = None
        s.queue_render(fast=False, now=True)

    def wheel(s, e):
        """Estilo Affinity: Ctrl + roda = zoom no ponto do cursor · roda = rolar para cima/baixo · Shift + roda = rolar para os lados."""
        if not s.prev:
            return "break"
        num, delta = getattr(e, "num", 0), getattr(e, "delta", 0)
        steps = 1.0 if num == 4 else -1.0 if num == 5 else delta / 120.0
        if not steps:
            return "break"
        x, y = e.x_root - s.cv.winfo_rootx(), e.y_root - s.cv.winfo_rooty()   # cursor dentro da folha, venha o evento de onde vier
        cw, ch = s.cv.winfo_width(), s.cv.winfo_height()
        if not (0 <= x < cw and 0 <= y < ch):
            return None
        if e.state & 0x4:                 # Ctrl segurado: zoom
            s.zoom_at(1.18 ** steps, x, y)
        elif s.zoom > 1:                  # sem Ctrl: rolar (no tamanho "ajustado" não há para onde rolar)
            lx, ly = s._pan_limits()
            unit = max(theme.px(40), int(ch * 0.10))
            if e.state & 0x1:             # Shift: para os lados
                s.px = max(-lx, min(lx, s.px + steps * unit))
            else:
                s.py = max(-ly, min(ly, s.py + steps * unit))
            s.queue_render(fast=True)
        return "break"

    def pan_start(s, e):
        s.cv.focus_set()
        s.drag = (e.x, e.y)
        s._click_start = (e.x, e.y)
        s._click_moved = False
        if s.prev and s.zoom > 1:   # o que está desenhado já respeita os limites: prende a posição guardada a eles também
            lx, ly = s._pan_limits()
            s.px, s.py = max(-lx, min(lx, s.px)), max(-ly, min(ly, s.py))

    def pan_move(s, e):
        if not (s.drag and s.zoom > 1 and s.prev):
            return
        dx, dy = e.x - s.drag[0], e.y - s.drag[1]
        if not dx and not dy:
            return
        if s._click_start is not None:
            sx, sy = s._click_start
            # Um pequeno movimento ainda é considerado clique; acima de 6 px é pan.
            s._click_moved = s._click_moved or ((e.x - sx) ** 2 + (e.y - sy) ** 2 > 36)
        s.drag = (e.x, e.y)
        lx, ly = s._pan_limits()
        nx, ny = max(-lx, min(lx, s.px + dx)), max(-ly, min(ly, s.py + dy))
        dx, dy = nx - s.px, ny - s.py     # quanto a folha andou de verdade (o limite pode segurar)
        s.px, s.py = nx, ny
        # O pan só move o bitmap já desenhado; não recria imagem nenhuma.
        if s._view_item is not None and (dx or dy):
            s.cv.move("view", dx, dy)
        # O bitmap tem uma sobra (buffer) de cada lado: renova ANTES de ela acabar. Antes só renovava depois que a borda
        # já tinha aparecido (e, com zoom, quase nunca), e a folha "sumia" nas bordas durante o arraste.
        ox, oy = s.px - s._tile_pan[0], s.py - s._tile_pan[1]
        lim = s._view_buffer * 0.35
        if abs(ox) > lim or abs(oy) > lim:
            s.queue_render(fast=True)

    def pan_end(s, e=None):
        s.drag = None
        if s.zoom > 1:
            s.queue_render(fast=True)   # um desenho rápido agora e o de qualidade logo depois

    def pan_end_click(s, e=None):
        # Clique simples na prévia = seleciona o botton correspondente na lista.
        moved = s._click_moved
        start = s._click_start
        s.pan_end(e)
        s._click_start = None
        s._click_moved = False
        if e is not None and start is not None and not moved:
            s.select_button_at(e.x, e.y)

    def select_button_at(s, cx, cy):
        """Converte um clique na folha para o botton daquela posição e seleciona-o na lista.

        A página pode estar com zoom e pan, então a conversão usa exatamente a mesma
        transformação usada pelo renderizador. Se o clique cair fora do círculo de um
        botton, nada é selecionado.
        """
        if not s.prev or not s.geom or not s.prevs:
            return
        transform = getattr(s, "_view_transform", None)
        if not transform or transform[0] != s.page or transform[1] != s.ver:
            return
        _, _, left, top, k = transform
        if k <= 0:
            return
        # Coordenadas da tela -> milímetros da folha.
        mx = (cx - left) / k
        my = (cy - top) / k
        W, H, total, gap = s.geom
        if mx < 0 or my < 0 or mx > W or my > H:
            return

        idx = s.sheet_items()
        pg = s._positions_cached(len(idx))
        page_slots = pg[min(s.page, len(pg) - 1)] if pg else []
        best = None
        best_d2 = float("inf")
        radius = total / 2.0
        for ii, x, y in page_slots:
            bx, by = x + radius, y + radius
            d2 = (mx - bx) ** 2 + (my - by) ** 2
            if d2 <= radius * radius and d2 < best_d2:
                best_d2 = d2
                best = idx[ii]
        if best is None or best >= len(s.items):
            return

        # Seleciona, garante que a linha fique visível e dá um pequeno destaque visual.
        s.lb.selection_clear(0, "end")
        s.lb.selection_set(best)
        s.lb.activate(best)
        s.lb.see(best)
        s.update_selhint(f"Botton #{best + 1} selecionado pela folha. Agora você pode ajustar o recorte manualmente.")
        s._flash_selected_list(best)

    def _flash_selected_list(s, index):
        """Dá um destaque curto à linha selecionada sem depender de cores fixas do tema."""
        try:
            s.lb.selection_anchor(index)
            s.after(80, lambda: s.lb.see(index) if s.winfo_exists() else None)
        except tk.TclError:
            pass

    def canvas_configure(s, e=None):
        """Redimensionamento da janela pode disparar dezenas de <Configure>; agrupa tudo em um render."""
        if s._resize_job:
            try:
                s.after_cancel(s._resize_job)
            except tk.TclError:
                pass
        s._resize_job = s.after(70, s.show)

    def show(s):
        if not s.prev:
            s._invalidate_view()
            s.cv.delete("all")
            theme.paint_stage(s.cv)
            theme.empty_state(s.cv)
            return
        cw, ch = max(s.cv.winfo_width(), 50), max(s.cv.winfo_height(), 50)
        key = (s.page, s.ver, round(s.zoom, 4), cw, ch,
               id(s.hi[1]) if s.hi and s.hi[0][:2] == (s.page, s.ver) else id(s.prev),
               bool(s.shownum), s.bg.get())
        if s._view_key == key and s.cv.find_withtag("view"):
            return
        # Para alterações de página/configuração, renderiza imediatamente; para zoom, o agendador cuida do debounce.
        s._view_force_key = key
        if s._view_job is None:
            s._render_view_tile()

    def export(s):
        if not s.check_sheet("Exportar"):
            return
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf"), ("PNG", "*.png")])
        if p:
            dpi = int(s.dpi.get())
            pg = s.pages(dpi)
            export(pg, p, dpi, s.bgrgba())
            extra = " (PNG: um arquivo por página, com _1, _2...)" if len(pg) > 1 and p.lower().endswith(".png") else ""
            messagebox.showinfo("Exportar", f"Arquivo salvo com {len(pg)} página(s).{extra}")

    # ---------- imprimir ----------
    def print_sheet(s):
        """Janelinha de impressão: imprime direto na impressora padrão ou abre o PDF para escolher a impressora."""
        n = len(s.sheet_items())
        if not s.check_sheet("Imprimir"):
            return
        s.audio.play_click()
        pg_warn = f"⚠ ATENÇÃO: serão impressas {len(s.prevs)} folhas de papel.\n\n" if len(s.prevs) > 1 else ""
        w = tk.Toplevel(s)
        w.title("Imprimir")
        w.configure(bg=theme.PANEL)
        w.transient(s)
        w.resizable(False, False)
        f = ttk.Frame(w, padding=18)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Imprimir folha", style="Sec.TLabel").pack(anchor="w")
        ttk.Label(f, style="Info.TLabel", justify="left", wraplength=theme.wrap(340),
                  text=pg_warn + f"{len(s.prevs)} página(s) · {n} botton(s) · folha {s.sheet.get()} · {s.dpi.get()} DPI.\n\n"
                       "Para os bottons saírem no tamanho certo, imprima em 100% / \"Tamanho real\" "
                       "(sem \"Ajustar à página\").").pack(anchor="w", pady=(6, 14))
        win = sys.platform == "win32"
        ttk.Label(f, style="Info.TLabel", justify="left", wraplength=theme.wrap(340),
                  text="Configurações da impressora: abre a janela do Windows com as preferências do driver "
                       "(papel, qualidade, cor, sem bordas…).").pack(anchor="w", pady=(0, 10))
        ttk.Button(f, text="Configurações da impressora…", style="Accent.TButton",
                   state="normal" if win else "disabled", command=lambda: s.do_driver_print(w)).pack(fill="x")
        ttk.Button(f, text="Imprimir agora (impressora padrão)",
                   command=lambda: s.do_print(w, direct=True)).pack(fill="x", pady=(6, 0))
        ttk.Button(f, text="Escolher impressora… (abre o PDF)",
                   command=lambda: s.do_print(w, direct=False)).pack(fill="x", pady=(6, 0))
        ttk.Button(f, text="Cancelar", command=w.destroy).pack(fill="x", pady=(6, 0))
        w.update_idletasks()
        w.geometry(f"+{s.winfo_rootx() + (s.winfo_width() - w.winfo_width()) // 2}"
                   f"+{s.winfo_rooty() + (s.winfo_height() - w.winfo_height()) // 3}")
        w.grab_set()
        w.bind("<Escape>", lambda e: w.destroy())

    def print_file(s):
        """Gera o PDF da folha numa pasta temporária (apaga os com mais de 1 dia) e devolve o caminho."""
        folder = os.path.join(tempfile.gettempdir(), "FolhaDeBottons_impressao")
        os.makedirs(folder, exist_ok=True)
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            try:
                if time.time() - os.path.getmtime(p) > 86400:
                    os.remove(p)
            except OSError:
                pass
        dpi = int(s.dpi.get())
        path = os.path.join(folder, f"folha_{datetime.datetime.now():%Y%m%d_%H%M%S}.pdf")
        export(s.pages(dpi), path, dpi, s.bgrgba())
        return path

    def do_driver_print(s, win):
        """Diálogo de impressão do Windows (com as Propriedades do driver, ex.: HP Smart Tank) e impressão em tamanho real."""
        win.destroy()
        import ctypes
        import winprint
        s.config(cursor="watch")
        s.update_idletasks()
        try:
            pg = s.pages(int(s.dpi.get()))
        finally:
            s.config(cursor="")
        W, H = s.geom[0], s.geom[1]
        hwnd = ctypes.windll.user32.GetParent(s.winfo_id()) or s.winfo_id()   # janela "de verdade" do Windows
        try:
            winprint.print_pages(pg, W, H, hwnd, s.print_state,
                                 confirm=lambda m: messagebox.askyesno("Imprimir", m, parent=s))
        except winprint.PrintCancelled:
            pass
        except Exception as ex:
            log_error(traceback.format_exc())
            messagebox.showerror("Imprimir", f"Não foi possível imprimir:\n\n{ex}", parent=s)

    def do_print(s, win, direct):
        win.destroy()
        s.config(cursor="watch")
        s.update_idletasks()
        try:
            path = s.print_file()
        finally:
            s.config(cursor="")
        if sys.platform == "win32":
            if direct:
                try:
                    os.startfile(path, "print")   # usa o programa de PDF padrão (Edge, Adobe...) e a impressora padrão
                    return
                except OSError:
                    messagebox.showinfo("Imprimir", "O Windows não tem um programa de PDF configurado para imprimir direto. "
                                                    "O PDF será aberto: use Ctrl+P.")
            try:
                os.startfile(path)
            except OSError:
                messagebox.showinfo("Imprimir", f"PDF salvo em:\n{path}\n\nAbra-o e imprima em 100%.")
        else:
            import subprocess
            try:
                subprocess.Popen(["lp", path] if direct else ["xdg-open", path])
            except OSError:
                messagebox.showinfo("Imprimir", f"PDF salvo em:\n{path}\n\nAbra-o e imprima em 100%.")


def _dpi_aware():
    """No Windows, evita interface borrada em telas com escala 125%/150%/200%."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


if __name__ == "__main__":
    sys.excepthook = crash
    _dpi_aware()
    App().mainloop()
