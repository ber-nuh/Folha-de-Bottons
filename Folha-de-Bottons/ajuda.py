"""Ajuda do Folha de Bottons: dicas ao passar o mouse, introdução da primeira vez e conteúdo da aba "Ajuda"."""
import tkinter as tk
from tkinter import ttk

import theme
from layout import positions


# ---------- dicas ao passar o mouse ----------
class Tooltip:
    """Balãozinho de explicação que aparece depois de meio segundo com o mouse parado sobre o widget."""

    def __init__(s, widget, text, delay=500):
        s.w, s.text, s.delay, s.tip, s.job = widget, text, delay, None, None
        widget.bind("<Enter>", s._enter, add="+")
        widget.bind("<Leave>", s._hide, add="+")
        widget.bind("<ButtonPress>", s._hide, add="+")

    def _enter(s, e=None):
        s._hide()
        s.job = s.w.after(s.delay, s._show)

    def _show(s):
        s.job = None
        try:
            if not s.w.winfo_exists():
                return
            s.tip = tk.Toplevel(s.w)
            s.tip.wm_overrideredirect(True)
            s.tip.attributes("-topmost", True)
            tk.Label(s.tip, text=s.text, justify="left", bg=theme.CARD, fg=theme.TEXT, relief="solid", bd=1,
                     padx=theme.px(8), pady=theme.px(5), wraplength=theme.wrap(290),
                     font=(theme.F, theme.fsize())).pack()
            s.tip.update_idletasks()
            tw, th = s.tip.winfo_width(), s.tip.winfo_height()
            x, y = s.w.winfo_rootx() + 12, s.w.winfo_rooty() + s.w.winfo_height() + 6
            if x + tw > s.w.winfo_screenwidth():
                x = s.w.winfo_screenwidth() - tw - 4
            if y + th > s.w.winfo_screenheight():
                y = s.w.winfo_rooty() - th - 6
            s.tip.geometry(f"+{x}+{y}")
        except tk.TclError:
            s.tip = None

    def _hide(s, e=None):
        if s.job:
            s.w.after_cancel(s.job)
            s.job = None
        if s.tip:
            try:
                s.tip.destroy()
            except tk.TclError:
                pass
            s.tip = None


# ---------- textos da aba Ajuda ----------
HELP = [
    ("Como usar (passo a passo)",
     "1. Clique em “Selecionar imagem” e escolha uma ou várias imagens com os seus bottons (PNG, JPG ou WEBP).\n"
     "2. Para acrescentar outras folhas sem apagar as atuais, use “+ Adicionar folhas”. O programa detecta os bottons e junta os tipos parecidos.\n"
     "3. Na aba “Quantidades”, diga quantos bottons de cada tipo você quer.\n"
     "4. Escolha o tamanho, o espaçamento e a posição na folha.\n"
     "5. Clique em “Exportar” (PDF ou PNG) ou em “Imprimir”."),
    ("Borda e efeito de vidro",
     "Nos temas modernos, a borda externa da janela fica invisível e os cantos são arredondados, e a janela fica levemente "
     "translúcida (efeito vidro): dá para ver um pouco do que está atrás dela. A intensidade varia conforme o tema "
     "(Verde esmeralda e Azul profundo são os mais transparentes). O Alto contraste e o Windows 95 clássico deixam a janela totalmente opaca."),
    ("Tamanho do botton",
     "O número (32 ou 58 mm) é o tamanho da arte. Em volta dela o programa acrescenta um contorno de 5 mm por lado "
     "(a parte que dobra por trás do pin), então o botton inteiro mede 42 mm ou 68 mm. É esse tamanho total que "
     "ocupa espaço na folha."),
    ("Espaçamento: por que importa",
     "É a distância, em milímetros, entre um botton e outro. Quanto menor, mais bottons cabem na folha. Com "
     "espaçamento 0 os contornos se encostam e, às vezes, cabe uma coluna ou linha a mais.\n\n"
     "Exemplo (folha A4, posição “Canto superior”): bottons de 58 mm ficam em 2 colunas com espaçamento 3 mm "
     "e em 3 colunas com espaçamento 0.\n\n"
     "Na aba “Bottons”, o texto logo abaixo da posição sempre mostra quantas colunas e linhas cabem e dá uma dica "
     "quando dá para encaixar mais."),
    ("Posição na folha",
     "Centralizados: o bloco de bottons fica no meio da folha, com margem de 5 mm.\n\n"
     "Canto superior: começa no canto de cima, à esquerda, e usa só 3 mm de folga nas bordas, o que pode "
     "encaixar uma coluna a mais (3 bottons de 58 mm na A4). Se a sua impressora não alcança tão perto da borda e "
     "corta o contorno, volte para “Centralizados”."),
    ("Mais de uma página",
     "Quando os bottons não cabem em uma folha, o programa cria páginas extras sozinho. Isso aparece em três lugares: "
     "na barra “Página 1 de 2” embaixo da pré-visualização, no texto abaixo do zoom e na janela de impressão "
     "(“serão impressas N folhas”).\n\n"
     "Troque de página com ◀ ▶, com os botões “Página” ou com PgUp/PgDn. Exportar em PDF gera um arquivo com todas "
     "as páginas; em PNG, um arquivo por página (_1, _2...)."),
    ("Ajustando um botton",
     "Clique no botton na lista. Depois: ◀ ▶ ▲ ▼ movem o recorte; + aproxima e − afasta; ⟲ ⟳ giram. “Cor do "
     "contorno” abre o seletor de cor. “Conta-gotas” abre uma janela própria para escolher a cor diretamente da imagem: "
     "mova o cursor para ver a amostra e os valores HEX/RGB e clique para aplicar a cor ao aro de 5 mm. A janela usa "
     "um painel fixo para evitar tremelicar durante o movimento do mouse. Esc ou botão direito cancela. “Cor automática” "
     "volta à cor calculada. “Cortar margem do selecionado” tira a borda branca em volta da arte.\n\nPasse o mouse sobre "
     "qualquer botão e espere meio segundo: aparece uma explicação."),
    ("Quantidades e tipos",
     "Bottons com a mesma arte formam um tipo. Na aba “Quantidades”, escolha quantos de cada tipo vão para a folha "
     "(0 = nenhum). Se o programa juntar bottons diferentes, diminua a Tolerância e clique em “Reagrupar”; se "
     "separar bottons iguais, aumente."),
    ("Pré-visualização",
     "Ctrl + roda do mouse: zoom no ponto do cursor (como no Affinity). Roda: rolar para cima e para baixo. "
     "Shift + roda: rolar para os lados. Arrastar com o botão esquerdo ou o do meio (com zoom): mover a folha. "
     "Duplo clique na folha ou clique na porcentagem do zoom: voltar ao tamanho que cabe na tela. "
     "F11: tela cheia (Esc sai). “Mostrar numeração” coloca o # de cada botton sobre a folha."),
    ("Imprimindo no tamanho certo",
     "Imprima sempre em 100% / “Tamanho real” (nunca “Ajustar à página”), senão os bottons saem menores. Use "
     "“Configurações da impressora…” para escolher papel, qualidade e “sem bordas”.\n\n"
     "Toda impressora tem uma margem que não alcança (em geral 3 a 5 mm). Se os bottons das bordas saírem "
     "cortados, use “Centralizados” ou aumente o espaçamento."),
    ("Letras maiores e alto contraste",
     "Se as letras estiverem pequenas ou difíceis de ler, abra a aba “Configurações”, em “Aparência”:\n\n"
     "• Tamanho do texto: Normal, Grande (125%), Muito grande (150%) ou Gigante (175%). Aumenta todas as letras "
     "do programa de uma vez; o painel da esquerda fica mais largo e, se a tela permitir, a janela cresce junto.\n"
     "• Alto contraste: letras em preto ou branco puro, bordas mais marcadas e sem transparência, em qualquer tema.\n\n"
     "As duas escolhas são salvas e voltam na próxima vez. As janelinhas do próprio Windows (abrir arquivo, "
     "escolher cor, impressora) seguem o tamanho de letra do Windows."),
    ("Configurações e atalhos",
     "Na aba “Configurações” ficam o tema, o tamanho do texto, o alto contraste, a música de fundo, o som de clique "
     "e o volume; tudo é salvo automaticamente. Coloque seus MP3/WAV nas pastas “musica” e “efeito”, ao lado do programa.\n\n"
     "F1: abrir esta Ajuda · F11: tela cheia · Ctrl + / Ctrl −: zoom · Ctrl 0: ajustar à tela."),
]


def build_help(parent, app):
    """Preenche a aba "Ajuda"."""
    wl = theme.wrap(270)
    ttk.Label(parent, text="Ajuda", style="Sec.TLabel").pack(anchor="w")
    ttk.Label(parent, style="Info.TLabel", wraplength=wl, justify="left",
              text="Tudo o que o programa faz, em ordem. Atalho: F1.").pack(anchor="w", pady=(0, 8))
    ttk.Button(parent, text="▶ Rever a introdução", style="Accent.TButton", command=app.show_intro).pack(fill="x")
    for title, body in HELP:
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(14, 8))
        ttk.Label(parent, text=title, style="Sec.TLabel", wraplength=wl, justify="left").pack(anchor="w")
        ttk.Label(parent, text=body, wraplength=wl, justify="left").pack(anchor="w", pady=(4, 0))


# ---------- introdução da primeira vez ----------
def _sheet(c, x, y, wpx, W, H, pos, total, label):
    """Desenha uma folha em miniatura com os bottons nas posições reais calculadas pelo layout."""
    k = wpx / W
    c.create_rectangle(x, y, x + W * k, y + H * k, fill="#ffffff", outline=theme.LINE)
    for _, bx, by in pos:
        c.create_oval(x + bx * k, y + by * k, x + (bx + total) * k, y + (by + total) * k,
                      fill=theme.ACC, outline=theme.ACC_HOVER)
    c.create_text(x + W * k / 2, y + H * k + theme.px(14), text=label, fill=theme.TEXT, justify="center",
                  font=(theme.F, theme.fsize(1.25), "bold"))


def _art_spacing(c, w, h):
    sh = theme.px(150)
    ww = sh * 210 / 297
    a = positions(40, 68, 3, 210, 297, "topleft")[0]
    b = positions(40, 68, 0, 210, 297, "topleft")[0]
    gx = (w - 2 * ww) / 3
    top = theme.px(6)
    _sheet(c, gx, top, ww, 210, 297, a, 68, f"Espaçamento 3 mm\n{len(a)} por folha")
    _sheet(c, 2 * gx + ww, top, ww, 210, 297, b, 68, f"Espaçamento 0\n{len(b)} por folha")


def _art_pages(c, w, h):
    sh = theme.px(150)
    ww = sh * 210 / 297
    pg = positions(14, 68, 0, 210, 297, "topleft")
    gx = (w - 2 * ww) / 3
    top = theme.px(6)
    _sheet(c, gx, top, ww, 210, 297, pg[0], 68, f"Página 1\n{len(pg[0])} bottons")
    _sheet(c, 2 * gx + ww, top, ww, 210, 297, pg[1], 68, f"Página 2\n{len(pg[1])} bottons")
    c.create_text(w / 2, top + sh / 2, text="▶", fill=theme.MUTED, font=(theme.F, 20, "bold"))


def _art_badge(txt):
    def draw(c, w, h):
        r = theme.px(55)
        c.create_oval(w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r, fill=theme.ACC, outline=theme.ACC_HOVER, width=3)
        c.create_oval(w / 2 - r * .7, h / 2 - r * .7, w / 2 + r * .7, h / 2 + r * .7, outline=theme.ACC_FG, width=2)
        c.create_text(w / 2, h / 2, text=txt, fill=theme.ACC_FG, font=(theme.F, 30, "bold"))
    return draw


SLIDES = [
    ("Bem-vindo ao Folha de Bottons!",
     "Este programa pega uma imagem com seus bottons, recorta cada um em círculo, acrescenta o contorno e "
     "organiza tudo em folhas prontas para exportar ou imprimir.\n\nEsta introdução rápida mostra como usar. "
     "Você pode revê-la quando quiser na aba “Ajuda”.\n\nLetras pequenas? Em “Configurações” há “Tamanho do texto” "
     "e “Alto contraste”.", _art_badge("★")),
    ("Passo 1 · Escolha uma ou várias folhas",
     "Clique em “Selecionar imagem” (canto superior esquerdo) e escolha uma ou várias fotos/folhas com os bottons desenhados, "
     "de preferência sobre fundo liso.\n\nPara acrescentar mais folhas depois, use “+ Adicionar folhas”. O programa mantém a seleção atual e incorpora os bottons detectados."
     " Se algum botton não for detectado, selecione a folha correspondente em “Folha ativa para ajustes manuais” e use “Adicionar”.", _art_badge("1")),
    ("Passo 2 · Confira e defina as quantidades",
     "Na lista “Bottons detectados”, clique em um botton para ajustar o recorte, girar ou trocar a cor do contorno. "
     "Passe o mouse sobre os botões para ver o que fazem.\n\nNa aba “Quantidades” escolha quantos de cada tipo de "
     "botton você quer na folha.", _art_badge("2")),
    ("Passo 3 · Espaçamento muda quantos cabem",
     "O espaçamento é a distância entre os bottons. Menos espaço = mais bottons por folha. Com 0 eles se encostam "
     "e pode caber uma coluna a mais (veja: bottons de 58 mm na A4).\n\nO programa avisa quantas colunas cabem e "
     "dá dicas para encaixar mais.", _art_spacing),
    ("Passo 4 · Mais de uma folha",
     "Se os bottons não cabem em uma folha, o programa cria páginas extras automaticamente.\n\nVocê vê isso na barra "
     "“Página 1 de 2” sobre a pré-visualização. Use ◀ ▶ para passar de uma página para outra. Ao imprimir, o "
     "programa avisa quantas folhas serão usadas.", _art_pages),
    ("Passo 5 · Exporte ou imprima",
     "“Exportar” salva um PDF (todas as páginas) ou PNG. “Imprimir” abre as opções da impressora.\n\nImprima "
     "sempre em 100% / “Tamanho real”, senão os bottons saem menores. Dúvidas? Aba “Ajuda” ou tecla F1.",
     _art_badge("✔")),
]


class Intro(tk.Toplevel):
    """Janela de boas-vindas (passo a passo com ilustrações). Chama on_close() ao terminar ou fechar."""

    def __init__(s, app, on_close):
        super().__init__(app)
        s.app, s.i, s.on_close, s.done = app, 0, on_close, False
        s.title("Bem-vindo ao Folha de Bottons")
        s.configure(bg=theme.PANEL)
        s.transient(app)
        s.resizable(False, False)
        s.protocol("WM_DELETE_WINDOW", s.finish)
        body = ttk.Frame(s, padding=theme.px(20))
        body.pack(fill="both", expand=True)
        s.count = ttk.Label(body, style="Info.TLabel")
        s.count.pack(anchor="w")
        s.head = ttk.Label(body, style="Sec.TLabel", font=(theme.F, theme.fz(theme.FONT_SIZE + 4, 1.5), "bold"))
        s.head.pack(anchor="w", pady=(2, 8))
        s.cw = theme.px(500 * min(theme.TEXT_SCALE, 1.5))   # texto maior => janela mais larga (mesmas linhas)
        s.cv = tk.Canvas(body, width=s.cw, height=theme.px(215), bg=theme.PANEL, highlightthickness=0, bd=0)
        s.cv.pack()
        tf = ttk.Frame(body, width=s.cw)
        tf.pack(pady=(8, 10))
        s.text = ttk.Label(tf, wraplength=s.cw, justify="left")
        s.text.pack(anchor="nw")
        tall = theme.px(150)   # altura = a do slide com mais texto: nada é cortado e a janela não "pula" entre os slides
        for _, txt, _ in SLIDES:
            s.text.config(text=txt)
            s.update_idletasks()
            tall = max(tall, s.text.winfo_reqheight())
        tf.config(height=tall)
        tf.pack_propagate(False)
        nav = ttk.Frame(body)
        nav.pack(fill="x")
        s.skip = ttk.Button(nav, text="Pular introdução", command=s.finish)
        s.skip.pack(side="left")
        s.nxt = ttk.Button(nav, text="Próximo ▶", style="Accent.TButton", command=lambda: s.go(1))
        s.nxt.pack(side="right")
        s.prv = ttk.Button(nav, text="◀ Voltar", command=lambda: s.go(-1))
        s.prv.pack(side="right", padx=(0, 6))
        s.bind("<Escape>", lambda e: s.finish())
        s.bind("<Right>", lambda e: s.go(1))
        s.bind("<Left>", lambda e: s.go(-1))
        s.render()
        s.update_idletasks()
        s.geometry(f"+{app.winfo_rootx() + max(0, (app.winfo_width() - s.winfo_width()) // 2)}"
                   f"+{app.winfo_rooty() + max(0, (app.winfo_height() - s.winfo_height()) // 3)}")
        s.grab_set()
        s.focus_set()

    def render(s):
        title, text, art = SLIDES[s.i]
        n = len(SLIDES)
        s.count.config(text=f"{s.i + 1} de {n}")
        s.head.config(text=title)
        s.text.config(text=text)
        s.cv.delete("all")
        art(s.cv, s.cw, theme.px(215))
        s.prv.state(["!disabled" if s.i else "disabled"])
        s.nxt.config(text="Começar! ✔" if s.i == n - 1 else "Próximo ▶")

    def go(s, d):
        if s.done:
            return
        if d > 0 and s.i == len(SLIDES) - 1:
            s.finish()
            return
        j = max(0, min(len(SLIDES) - 1, s.i + d))
        if j != s.i:
            s.i = j
            s.app.audio.play_click()
            s.render()

    def finish(s):
        if s.done:
            return
        s.done = True
        try:
            s.grab_release()
        except tk.TclError:
            pass
        s.destroy()
        s.on_close()


# Visual dos temas: no Windows 11, os temas modernos suprimem a borda DWM e usam cantos arredondados; o Windows 95 preserva a moldura clássica.
