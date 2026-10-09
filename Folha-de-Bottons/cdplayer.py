"""Leitor de MP3 no estilo do "CD Player" do Windows 95/98.

Aparece nas Configurações, na área de música, só nos temas com CD_PLAYER=True (Windows 95 clássico).
Mostra o visor "[faixa] tempo", os botões Play / Pause / Stop / faixa anterior / voltar / avançar /
próxima faixa / ejetar, os campos Artista / Título / Faixa e a barra de status (Total / Faixa).
Usa o AudioManager (audio.py); as músicas são as da pasta "musica".
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

import theme

BG, HI, LT, SH, DK = "#C0C0C0", "#FFFFFF", "#DFDFDF", "#808080", "#000000"   # cores do chanfro 3D clássico
NAVY, SKY = "#000080", "#1084D0"                                             # barra de título (degradê do Win98)
LCD_BG, LCD_FG = "#000000", "#808000"                                        # visor: preto com dígitos verde-oliva

# ícones dos botões, em "pontos" a partir do centro: ("p", polígono) ou ("r", retângulo x0, y0, x1, y1)
ICONS = {
    "play":  [("p", [(-3, -5), (-3, 5), (4, 0)])],
    "pause": [("r", (-4, -5, -1, 5)), ("r", (1, -5, 4, 5))],
    "stop":  [("r", (-4, -4, 4, 4))],
    "prev":  [("r", (-6, -4, -4, 4)), ("p", [(0, -4), (0, 4), (-4, 0)]), ("p", [(4, -4), (4, 4), (0, 0)])],
    "rew":   [("p", [(-1, -4), (-1, 4), (-5, 0)]), ("p", [(4, -4), (4, 4), (0, 0)])],
    "fwd":   [("p", [(-4, -4), (-4, 4), (0, 0)]), ("p", [(0, -4), (0, 4), (4, 0)])],
    "next":  [("p", [(-4, -4), (-4, 4), (0, 0)]), ("p", [(0, -4), (0, 4), (4, 0)]), ("r", (4, -4, 6, 4))],
    "eject": [("p", [(-5, 1), (5, 1), (0, -5)]), ("r", (-5, 3, 5, 5))],
    "min":   [("r", (-4, 3, 3, 5))],
    "down":  [("p", [(-3, -1), (3, -1), (0, 2)])],
}


class _Btn(tk.Canvas):
    """Botão com chanfro 3D do Windows 95 e ícone desenhado (afunda ao clicar; ícone 'em relevo' quando desativado)."""

    def __init__(self, parent, icon, command, w, h, bg=BG):
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, bd=0)
        self.icon, self.command = icon, command
        self.enabled, self.down, self.inside = True, False, False
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<Configure>", lambda e: self.draw())
        self.draw()

    def set_enabled(self, on):
        if self.enabled != bool(on):
            self.enabled = bool(on)
            self.draw()

    def _press(self, e):
        if self.enabled:
            self.down = self.inside = True
            self.draw()

    def _hover(self, inside):
        self.inside = inside
        if self.down:
            self.draw()   # arrastou para fora: desafunda; voltou: afunda de novo

    def _release(self, e):
        click = self.down and self.inside
        self.down = False
        self.draw()
        if click and self.command:
            self.command()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8:   # ainda não apareceu na tela: usa o tamanho pedido
            w, h = int(float(self.cget("width"))), int(float(self.cget("height")))
        t = theme.px(1)
        bar = lambda x0, y0, x1, y1, c: self.create_rectangle(x0, y0, x1, y1, fill=c, outline="")
        bar(0, 0, w, h, BG)
        pressed = self.down and self.inside
        if pressed:   # moldura preta + sombra cinza por dentro
            for c, i in ((DK, 0), (SH, t)):
                bar(i, i, w - i, i + t, c); bar(i, h - i - t, w - i, h - i, c)
                bar(i, i, i + t, h - i, c); bar(w - i - t, i, w - i, h - i, c)
        else:         # relevo: branco em cima/esquerda, preto embaixo/direita
            bar(w - t, 0, w, h, DK); bar(0, h - t, w, h, DK)
            bar(0, 0, w - t, t, HI); bar(0, 0, t, h - t, HI)
            bar(w - 2 * t, t, w - t, h - t, SH); bar(t, h - 2 * t, w - t, h - t, SH)
            bar(t, t, w - 2 * t, 2 * t, LT); bar(t, t, 2 * t, h - 2 * t, LT)
        off = t if pressed else 0
        cx, cy = w // 2 + off, h // 2 + off
        if self.enabled:
            self._icon(cx, cy, DK)
        else:
            self._icon(cx + t, cy + t, HI)
            self._icon(cx, cy, SH)

    def _icon(self, cx, cy, color):
        u = theme.px(1)
        for kind, pts in ICONS[self.icon]:
            if kind == "p":
                flat = [v for x, y in pts for v in (cx + x * u, cy + y * u)]
                self.create_polygon(flat, fill=color, outline=color)
            else:
                x0, y0, x1, y1 = pts
                self.create_rectangle(cx + x0 * u, cy + y0 * u, cx + x1 * u, cy + y1 * u, fill=color, outline="")


class CDPlayer(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG, bd=2, relief="raised")   # moldura da "janela"
        self.app = app
        self.names, self.labels, self.lengths = [], [], {}   # músicas da pasta, rótulos da caixa 'Faixa' e duração (ms) de cada uma
        self._probe_job, self._pending_refresh = None, False
        self.collapsed = False
        fams = set(tkfont.families(app))
        self.fl = (theme.F, theme.fsize(1.25))   # caixas de tamanho fixo: cresce só até 125%
        self.lcd_family = next((f for f in ("Arial", "Microsoft Sans Serif", theme.F) if f in fams), theme.F)
        self._lcd_fonts = {}
        self._build()
        app.bind("<FocusIn>", self._focus_in, add="+")   # voltou do Explorer (depois de ejetar): relê a pasta

    # ---------- montagem ----------
    def _build(self):
        px, app = theme.px, self.app
        # barra de título (degradê azul, como no Windows 98) + botão de recolher
        bar = tk.Frame(self, bg=SKY)
        bar.pack(fill="x", padx=px(1), pady=(px(1), 0))
        self.titlebar = tk.Canvas(bar, height=max(px(18), int(theme.fsize(1.25) * 1.333 * theme.S * 1.7)), bg=NAVY, highlightthickness=0, bd=0)
        self.titlebar.pack(side="left", fill="x", expand=True)
        self.titlebar.bind("<Configure>", self._draw_title)
        _Btn(bar, "min", self.toggle_body, px(16), px(14), bg=SKY).pack(side="right", padx=px(2), pady=px(2))

        # menus
        mb = tk.Frame(self, bg=BG)
        mb.pack(fill="x")
        self.menus = {}

        def menu(text, fill):
            b = tk.Menubutton(mb, text=text, bg=BG, fg=DK, activebackground=NAVY, activeforeground=HI,
                              relief="flat", bd=0, padx=px(6), pady=px(1), font=self.fl)
            m = tk.Menu(b, tearoff=0)
            fill(m)
            b.configure(menu=m)
            b.pack(side="left")
            self.menus[text] = m

        def disco(m):
            m.add_command(label='Abrir pasta "musica"', command=self.eject)
            m.add_command(label="Atualizar lista", command=self.refresh_btn)

        def exibir(m):
            for t, v in (("Tempo decorrido da faixa", "decorrido"), ("Tempo restante da faixa", "restante")):
                m.add_radiobutton(label=t, variable=app.cd_view, value=v, command=self.options_changed)

        def opcoes(m):
            m.add_checkbutton(label="Ordem aleatória", variable=app.cd_shuffle, command=self.options_changed)
            m.add_checkbutton(label="Repetir a mesma faixa", variable=app.cd_repeat, command=self.options_changed)

        menu("Disco", disco)
        menu("Exibir", exibir)
        menu("Opções", opcoes)
        menu("Ajuda", lambda m: m.add_command(label="Como adicionar músicas", command=self.help))

        # corpo
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="x", padx=px(5), pady=(px(4), px(5)))
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x")
        top.grid_columnconfigure(0, weight=1)

        # visor
        box = tk.Frame(top, bg=BG, bd=2, relief="sunken")
        box.grid(row=0, column=0, sticky="nsew", padx=(0, px(6)))
        self.lcd_in = tk.Frame(box, bg=LCD_BG, width=px(105), height=px(50))
        self.lcd_in.pack_propagate(False)
        self.lcd_in.pack(fill="both", expand=True)
        self.lcd = tk.Label(self.lcd_in, text="[00] 00:00", bg=LCD_BG, fg=LCD_FG, font=(self.lcd_family, 16))
        self.lcd.pack(expand=True)
        self.lcd_in.bind("<Configure>", self._fit_lcd)

        # botões: linha 1 = Play (largo), Pause, Stop; linha 2 = anterior, voltar, avançar, próxima, ejetar
        btns = tk.Frame(top, bg=BG)
        btns.grid(row=0, column=1)

        def mk(icon, cmd, r, c, span=1):
            b = _Btn(btns, icon, cmd, px(25), px(21))
            b.grid(row=r, column=c, columnspan=span, sticky="ew", padx=px(1), pady=px(1))
            return b

        self.buttons = [mk("play", self.play, 0, 0, 3), mk("pause", self.pause, 0, 3), mk("stop", self.stop, 0, 4),
                        mk("prev", self.prev, 1, 0), mk("rew", self.rew, 1, 1), mk("fwd", self.fwd, 1, 2),
                        mk("next", self.next, 1, 3)]
        self.b_eject = mk("eject", self.eject, 1, 4)   # sempre ativo: é por onde se colocam músicas na pasta

        # campos Artista / Título / Faixa
        form = tk.Frame(self.body, bg=BG)
        form.pack(fill="x", pady=(px(6), 0))
        form.grid_columnconfigure(1, weight=1)
        for r, t in enumerate(("Artista:", "Título:", "Faixa:")):
            tk.Label(form, text=t, bg=BG, fg=DK, font=self.fl, anchor="e").grid(
                row=r, column=0, sticky="e", padx=(0, px(6)), pady=px(2))

        af = tk.Frame(form, bg=HI, bd=2, relief="sunken", height=px(24))
        af.pack_propagate(False)
        af.grid(row=0, column=1, sticky="ew", pady=px(2))
        _Btn(af, "down", self.disc_menu, px(16), px(18), bg=HI).pack(side="right")
        tk.Label(af, text="<musica>", bg=HI, fg=DK, font=self.fl).pack(side="right", padx=px(3))
        self.artist = tk.Label(af, text="", bg=HI, fg=DK, font=self.fl, anchor="w")
        self.artist.pack(side="left", fill="x", expand=True, padx=px(2))

        tf = tk.Frame(form, bg=BG, bd=2, relief="sunken", height=px(24))
        tf.pack_propagate(False)
        tf.grid(row=1, column=1, sticky="ew", pady=px(2))
        self.song = tk.Label(tf, text="", bg=BG, fg=DK, font=self.fl, anchor="w")
        self.song.pack(fill="x", expand=True, padx=px(2))

        self.track_var = tk.StringVar()
        self.cb = ttk.Combobox(form, textvariable=self.track_var, state="readonly", width=10)
        self.cb.grid(row=2, column=1, sticky="ew", pady=px(2))
        self.cb.bind("<<ComboboxSelected>>", self._pick)

        # barra de status
        sb = tk.Frame(self.body, bg=BG)
        sb.pack(fill="x", pady=(px(6), 0))
        for c in (0, 1):
            sb.grid_columnconfigure(c, weight=1, uniform="status")
        self.st_total = tk.Label(sb, text="Total: 00:00 m:s", bg=BG, fg=DK, font=self.fl, anchor="w",
                                 bd=1, relief="sunken", padx=px(3))
        self.st_total.grid(row=0, column=0, sticky="ew", padx=(0, px(2)))
        self.st_track = tk.Label(sb, text="Faixa: 00:00 m:s", bg=BG, fg=DK, font=self.fl, anchor="w",
                                 bd=1, relief="sunken", padx=px(3))
        self.st_track.grid(row=0, column=1, sticky="ew")

    def _draw_title(self, e=None):
        c, px = self.titlebar, theme.px
        w, h = max(c.winfo_width(), 2), max(c.winfo_height(), 2)
        c.delete("all")
        n = min(w, 96)   # degradê em até 96 faixas
        a, b = (0, 0, 128), (16, 132, 208)
        for i in range(n):
            col = "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * i / max(n - 1, 1)) for k in range(3))
            c.create_rectangle(w * i // n, 0, w * (i + 1) // n + 1, h, fill=col, outline="")
        c.create_oval(px(4), h // 2 - px(6), px(16), h // 2 + px(6), fill=BG, outline=HI)   # mini CD
        c.create_oval(px(8), h // 2 - px(2), px(12), h // 2 + px(2), fill=NAVY, outline=SH)
        c.create_text(px(22), h // 2, anchor="w", text="Leitor de MP3", fill=HI,
                      font=(theme.F, theme.fsize(1.25), "bold"))

    def _fit_lcd(self, e=None):
        """Escolhe o maior tamanho de letra em que '[00] -00:00' ainda cabe no visor."""
        w = self.lcd_in.winfo_width() - theme.px(10)
        size = 10
        for size in (20, 18, 16, 14, 13, 12, 11, 10):
            f = self._lcd_fonts.get(size)
            if f is None:
                f = self._lcd_fonts[size] = tkfont.Font(family=self.lcd_family, size=size)
            if f.measure("[00] -00:00") <= w:
                break
        self.lcd.configure(font=(self.lcd_family, size))

    # ---------- lista e visor ----------
    def reload(self):
        """Relê as músicas da pasta (chamado quando a lista muda ou o leitor aparece)."""
        a = self.app.audio
        self.names = a.list_music()
        for k in [k for k in self.lengths if k not in self.names]:
            del self.lengths[k]
        self.labels = [f"{i + 1:02d}   {os.path.splitext(n)[0]}" for i, n in enumerate(self.names)]
        self.cb.configure(values=self.labels, state="readonly" if self.names else "disabled")
        for b in self.buttons:
            b.set_enabled(bool(self.names))
        self.refresh_display()
        self._probe_kick()

    @staticmethod
    def _fmt(ms):
        sign = "-" if ms < 0 else ""
        sec = abs(int(ms)) // 1000
        return f"{sign}{sec // 60:02d}:{sec % 60:02d}"

    @staticmethod
    def _set(widget, text):
        if widget.cget("text") != text:
            widget.configure(text=text)

    def refresh_display(self):
        app, a = self.app, self.app.audio
        cur = a.music_name()
        idx = self.names.index(cur) if cur in self.names else -1
        state = a.music_state()
        pos = a.music_position() if state != "stopped" else 0
        length = a.music_length() if state != "stopped" else 0
        if length and idx >= 0:
            self.lengths[cur] = length
        else:
            length = self.lengths.get(cur, 0) if idx >= 0 else 0
        shown = pos if app.cd_view.get() != "restante" else -max(0, length - pos)
        self._set(self.lcd, f"[{idx + 1:02d}] {self._fmt(shown)}")
        if idx < 0:
            self._set(self.artist, "Nenhum disco (pasta vazia)")
            self._set(self.song, 'Coloque MP3 ou WAV na pasta "musica".')
            if self.track_var.get():
                self.track_var.set("")
        else:
            base = os.path.splitext(cur)[0]
            artist, song = base.split(" - ", 1) if " - " in base else ("Desconhecido", base)
            self._set(self.artist, artist)
            self._set(self.song, song)
            if self.track_var.get() != self.labels[idx]:
                self.track_var.set(self.labels[idx])
        total = sum(self.lengths.get(n, 0) for n in self.names)
        self._set(self.st_total, f"Total: {self._fmt(total)} m:s")
        self._set(self.st_track, f"Faixa: {self._fmt(length)} m:s")

    def _probe_kick(self):
        """Mede a duração das músicas uma por vez (sem travar a janela) para preencher 'Total' e 'Faixa'."""
        if self._probe_job is None and any(n not in self.lengths for n in self.names):
            self._probe_job = self.after(60, self._probe_step)

    def _probe_step(self):
        self._probe_job = None
        a = self.app.audio
        for n in self.names:
            if n not in self.lengths:
                self.lengths[n] = a.probe_length(a.music_path(n))   # 0 = não conseguiu ler (não tenta de novo)
                break
        else:
            return
        self.refresh_display()
        self._probe_kick()

    # ---------- botões ----------
    def play(self):
        a = self.app.audio
        if not self.names:
            return
        state = a.music_state()
        if state == "paused":
            a.resume_music()
        elif state == "stopped":
            self.app.music_enabled.set(True)   # tocar = "Ativar música de fundo" ligado
            a.set_music_enabled(True)
            self.app.save_audio_config()
        a.play_click()
        self.refresh_display()

    def pause(self):
        a = self.app.audio
        state = a.music_state()
        if state == "playing":
            a.pause_music()
        elif state == "paused":
            a.resume_music()
        a.play_click()
        self.refresh_display()

    def stop(self):
        app = self.app
        if app.audio.music_state() != "stopped":
            app.music_enabled.set(False)   # parar = "Ativar música de fundo" desligado
            app.audio.set_music_enabled(False)
            app.save_audio_config()
        app.audio.play_click()
        self.refresh_display()

    def prev(self):
        a = self.app.audio
        a.play_click()
        if a.music_state() != "stopped" and a.music_position() > 3000:
            a.music_seek(0)   # passou de 3 s: volta ao começo da faixa; senão, vai para a anterior
        else:
            self.app.music_advance(-1)
        self.refresh_display()

    def next(self):
        self.app.audio.play_click()
        self.app.music_advance(1)
        self.refresh_display()

    def rew(self):
        a = self.app.audio
        a.play_click()
        a.music_seek(a.music_position() - 5000)
        self.refresh_display()

    def fwd(self):
        a = self.app.audio
        a.play_click()
        length = a.music_length()
        if a.music_state() != "stopped" and length and a.music_position() + 5000 >= length - 500:
            self.app.music_advance(1)
        else:
            a.music_seek(a.music_position() + 5000)
        self.refresh_display()

    def eject(self):
        """Ejetar = abrir a pasta "musica"; ao voltar para o programa, a lista é atualizada sozinha."""
        self.app.audio.play_click()
        self._pending_refresh = True
        self.app.open_folder(self.app.audio.music_dir)

    def destroy(self):
        if self._probe_job:   # cancela a leitura de durações em andamento (o leitor é recriado ao mudar o texto)
            try:
                self.after_cancel(self._probe_job)
            except Exception:
                pass
        super().destroy()

    def _focus_in(self, e):
        if self._pending_refresh and e.widget is self.app:
            self._pending_refresh = False
            self.app.refresh_audio_lists()

    def refresh_btn(self):
        self.app.audio.play_click()
        self.app.refresh_audio_lists()

    def disc_menu(self):
        m = self.menus["Disco"]
        try:
            m.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            m.grab_release()

    def _pick(self, e=None):
        i = self.cb.current()
        if 0 <= i < len(self.names):
            self.app.audio.play_click()
            self.app.music_file.set(self.names[i])
            self.app.change_music_file()
            self.refresh_display()

    def options_changed(self):
        self.app.save_audio_config()
        self.refresh_display()

    def help(self):
        messagebox.showinfo(
            "Folha de Bottons",
            'Coloque arquivos MP3 ou WAV na pasta "musica" (ao lado do programa).\n\n'
            'O botão de ejetar (▲) abre a pasta e, quando você voltar ao programa, a lista é atualizada. '
            'Também dá para usar Disco > Atualizar lista.\n\n'
            'Parar desliga a música de fundo; Tocar liga de novo.')

    def toggle_body(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.body.pack_forget()
        else:
            self.body.pack(fill="x", padx=theme.px(5), pady=(theme.px(4), theme.px(5)))
        self.app.audio.play_click()
