"""Áudio do Folha de Bottons.
Usa o Windows Multimedia System (winmm/MCI), que permite música de fundo
e efeitos curtos simultaneamente sem instalar pygame ou outra biblioteca.

As músicas ficam na pasta "musica" e os efeitos de clique na pasta "efeito",
ao lado do programa. Qualquer arquivo colocado lá aparece nas Configurações.
"""
import os
import sys
import ctypes

# formatos que o Windows costuma tocar por este caminho (MP3 e WAV são os mais seguros)
EXTS = (".mp3", ".wav", ".wma", ".m4a", ".aac", ".mid")


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class AudioManager:
    MUSIC_FOLDER = "musica"
    CLICK_FOLDER = "efeito"
    # arquivos que já vinham com o programa (usados se as pastas ainda estiverem vazias)
    DEFAULT_MUSIC = "capzlock.mp3"
    DEFAULT_CLICK = "universfield-computer-mouse-click-352734.mp3"
    DEFAULT_VOLUME = 5   # volume de fábrica da música (%); o app.py usa este mesmo valor na primeira abertura

    def __init__(self):
        self.base = _base_dir()
        self.music_dir = os.path.join(self.base, self.MUSIC_FOLDER)
        self.click_dir = os.path.join(self.base, self.CLICK_FOLDER)
        for d in (self.music_dir, self.click_dir):   # cria as pastas se ainda não existirem
            try:
                os.makedirs(d, exist_ok=True)
            except OSError:
                pass
        # sem escolha salva: usa o arquivo padrão se existir, senão o primeiro da pasta
        self.music = self._resolve(self.music_dir, self.DEFAULT_MUSIC, self.list_music())
        self.click = self._resolve(self.click_dir, self.DEFAULT_CLICK, self.list_effects())
        self._opened = False         # música aberta no MCI
        self._click_opened = False   # efeito aberto no MCI
        self.paused = False          # música em pausa (botão Pause do leitor)
        self._stalled_ticks = 0      # leituras seguidas em que a posição da música não andou
        self._last_pos = None        # última posição lida (para saber se a música ainda anda)
        self._seen_progress = False  # já vimos a posição andar desde o último play?
        self.music_enabled = True
        self.click_enabled = True
        self.music_volume = self.DEFAULT_VOLUME

    # ---------- arquivos ----------
    def _list(self, folder, legacy):
        """Nomes dos arquivos de áudio da pasta (ordem alfabética). Pasta vazia: usa o arquivo antigo, se existir."""
        try:
            names = sorted((f for f in os.listdir(folder)
                            if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder, f))), key=str.lower)
        except OSError:
            names = []
        if not names and os.path.isfile(os.path.join(self.base, legacy)):
            names = [legacy]
        return names

    def list_music(self):
        return self._list(self.music_dir, self.DEFAULT_MUSIC)

    def list_effects(self):
        return self._list(self.click_dir, self.DEFAULT_CLICK)

    def _resolve(self, folder, name, available):
        """Caminho completo do arquivo 'name' na pasta. Se ele não existir, usa o padrão ou o primeiro da lista."""
        default = self.DEFAULT_MUSIC if folder == self.music_dir else self.DEFAULT_CLICK
        for cand in (name, default):
            if cand and os.path.isfile(os.path.join(folder, cand)):
                return os.path.join(folder, cand)
        if available:   # (pasta vazia + arquivo antigo ao lado do programa também cai aqui)
            first = os.path.join(folder, available[0])
            return first if os.path.isfile(first) else os.path.join(self.base, available[0])
        return os.path.join(folder, name or default)

    def _exact(self, folder, name, legacy):
        """Caminho do arquivo SÓ se ele estiver na lista da pasta (lista desatualizada => None)."""
        if name not in self._list(folder, legacy):
            return None
        p = os.path.join(folder, name)
        return p if os.path.isfile(p) else os.path.join(self.base, name)

    def music_name(self):
        return os.path.basename(self.music)

    def click_name(self):
        return os.path.basename(self.click)

    def use_files(self, music_name=None, click_name=None):
        """Define os arquivos escolhidos (lidos da configuração) sem tocar nada. Nome que sumiu da pasta é ignorado."""
        if music_name:
            self.music = self._resolve(self.music_dir, music_name, self.list_music())
        if click_name:
            self.click = self._resolve(self.click_dir, click_name, self.list_effects())

    # ---------- MCI ----------
    def _mci(self, command):
        if os.name != "nt":
            return 1
        try:
            return ctypes.windll.winmm.mciSendStringW(command, None, 0, 0)
        except Exception:
            return 1

    def _mci_text(self, command):
        """Como _mci, mas devolve também a resposta em texto: (código, texto)."""
        if os.name != "nt":
            return 1, ""
        try:
            buf = ctypes.create_unicode_buffer(256)
            code = ctypes.windll.winmm.mciSendStringW(command, buf, 255, 0)
            return code, buf.value
        except Exception:
            return 1, ""

    def _status_int(self, alias, item):
        code, txt = self._mci_text(f"status {alias} {item}")
        txt = txt.strip()
        return int(txt) if code == 0 and txt.isdigit() else 0

    def _open_click(self):
        if self._click_opened or os.name != "nt" or not os.path.exists(self.click):
            return
        click = self.click.replace('"', '""')
        # Cada áudio recebe seu próprio alias para poder tocar simultaneamente.
        if self._mci(f'open "{click}" type mpegvideo alias folhabottons_click') == 0:
            self._click_opened = True

    def start_music(self):
        self._open_click()   # o efeito de clique abre mesmo com a música desligada
        if not self.music_enabled or os.name != "nt" or not os.path.exists(self.music):
            return
        if self._opened:
            return
        music = self.music.replace('"', '""')
        if self._mci(f'open "{music}" type mpegvideo alias folhabottons_music') == 0:
            self._mci("set folhabottons_music time format milliseconds")
            self._mci(f"setaudio folhabottons_music volume to {max(0, min(100, int(self.music_volume))) * 10}")
            self._mci("play folhabottons_music")   # sem 'repeat' do MCI: music_ended() avisa o fim e o programa repete ou passa para a próxima faixa
            self._opened = True
            self.paused = False
            self._reset_end_watch()

    def play_click(self, force=False):
        """force=True toca mesmo com o som de clique desligado (usado na prévia ao escolher um efeito)."""
        if (not self.click_enabled and not force) or os.name != "nt" or not os.path.exists(self.click):
            return
        if not self._click_opened:
            self._open_click()
            if not self._click_opened:
                return
        # Reinicia o efeito sem interromper a música de fundo.
        self._mci("seek folhabottons_click to start")
        self._mci("setaudio folhabottons_click volume to 1000")
        self._mci("play folhabottons_click")

    def set_music_file(self, name):
        """Troca a música (e toca, se a música estiver ligada). Devolve False se o Windows não conseguiu abrir o arquivo."""
        path = self._exact(self.music_dir, name, self.DEFAULT_MUSIC)
        if not path:
            return False
        self.music = path
        if self._opened:
            self._mci("stop folhabottons_music")
            self._mci("close folhabottons_music")
            self._opened = False
        self.paused = False
        self._reset_end_watch()
        if self.music_enabled:
            self.start_music()
            return self._opened or os.name != "nt"
        return True

    def set_click_file(self, name):
        """Troca o efeito de clique. Devolve False se o Windows não conseguiu abrir o arquivo."""
        path = self._exact(self.click_dir, name, self.DEFAULT_CLICK)
        if not path:
            return False
        self.click = path
        if self._click_opened:
            self._mci("stop folhabottons_click")
            self._mci("close folhabottons_click")
            self._click_opened = False
        self._open_click()
        return self._click_opened or os.name != "nt"

    def set_music_enabled(self, enabled):
        self.music_enabled = bool(enabled)
        if self.music_enabled:
            if not self._opened:
                self.start_music()
            elif self.paused:
                self.resume_music()
            else:
                self._mci(f"setaudio folhabottons_music volume to {max(0, min(100, int(self.music_volume))) * 10}")
                self._mci("play folhabottons_music")
        elif self._opened:
            self._mci("stop folhabottons_music")
            self._mci("seek folhabottons_music to start")   # parar = voltar ao começo da faixa
            self.paused = False
            self._reset_end_watch()

    # ---------- controles do leitor (estilo CD Player) ----------
    def music_state(self):
        """"playing", "paused" ou "stopped"."""
        if not (self._opened and self.music_enabled):
            return "stopped"
        return "paused" if self.paused else "playing"

    def pause_music(self):
        if self.music_state() == "playing":
            self._mci("pause folhabottons_music")
            self.paused = True

    def resume_music(self):
        if self._opened and self.paused:
            self._reset_end_watch()
            if self._mci("resume folhabottons_music") != 0:
                self._mci("play folhabottons_music")
            self.paused = False

    def music_position(self):
        """Posição atual da faixa, em milissegundos (0 se parada)."""
        if self.music_state() == "stopped":
            return 0
        return self._status_int("folhabottons_music", "position")

    def music_length(self):
        """Duração da faixa aberta, em milissegundos (0 se não souber)."""
        if not self._opened:
            return 0
        return self._status_int("folhabottons_music", "length")

    def music_seek(self, ms):
        """Pula para 'ms' milissegundos (mantém a pausa, se estiver pausada)."""
        if self.music_state() == "stopped":
            return
        length = self.music_length()
        ms = max(0, int(ms))
        if length:
            ms = min(ms, max(0, length - 300))
        was_paused = self.paused
        self._reset_end_watch()
        self._mci(f"play folhabottons_music from {ms}")
        if was_paused:
            self._mci("pause folhabottons_music")

    def restart_music(self):
        """Toca a faixa atual de novo, do começo."""
        if not self.music_enabled:
            return
        if self._opened:
            self.paused = False
            self._reset_end_watch()
            if self._mci("play folhabottons_music from 0") != 0:
                # o Windows recusou voltar ao início (acontece depois do fim em alguns MP3): fecha e abre de novo
                self._mci("stop folhabottons_music")
                self._mci("close folhabottons_music")
                self._opened = False
                self.start_music()
        else:
            self.start_music()

    def _reset_end_watch(self):
        """Recomeça a observação do fim da faixa (depois de play, seek, pausa, troca de música...)."""
        self._stalled_ticks = 0
        self._last_pos = None
        self._seen_progress = False

    def music_ended(self):
        """True uma única vez quando a música que estava tocando chegou ao fim.

        O fim é percebido pela POSIÇÃO: se a música deveria estar tocando e a posição parou de andar, ela acabou.
        Isso não depende do texto que o Windows devolve em "status mode" (ele pode vir traduzido, ex.: "parado"),
        nem de a posição ficar no final da faixa: em alguns MP3/Windows ela volta a 0 quando termina.
        Só vale depois de vermos a posição andar ao menos uma vez, para não reiniciar à toa se a leitura falhar."""
        if self.music_state() != "playing" or os.name != "nt":
            self._reset_end_watch()
            return False
        pos = self._status_int("folhabottons_music", "position")
        if self._last_pos is None or pos != self._last_pos:   # andou (ou é a primeira leitura)
            if self._last_pos is not None and pos > 0:
                self._seen_progress = True
            self._last_pos = pos
            self._stalled_ticks = 0
            return False
        # a posição não andou desde a leitura anterior
        self._stalled_ticks += 1
        if not self._seen_progress:
            return False
        length = self.music_length()
        code, mode = self._mci_text("status folhabottons_music mode")
        explicit_stop = code == 0 and mode.strip().lower() == "stopped"   # só funciona com Windows em inglês; é um atalho
        near_end = length > 0 and pos >= length - 1500
        # alguns MP3 informam duração maior que a real, e a posição pode voltar a 0: 3 leituras paradas (~1 s) também valem
        if explicit_stop or near_end or self._stalled_ticks >= 3:
            self._reset_end_watch()
            return True
        return False

    def probe_length(self, path):
        """Duração (ms) de um arquivo, sem tocar. 0 se o Windows não conseguir ler."""
        if os.name != "nt" or not os.path.isfile(path):
            return 0
        p = path.replace('"', '""')
        if self._mci(f'open "{p}" type mpegvideo alias folhabottons_probe') != 0:
            return 0
        try:
            self._mci("set folhabottons_probe time format milliseconds")
            code, txt = self._mci_text("status folhabottons_probe length")
            return int(txt.strip()) if code == 0 and txt.strip().isdigit() else 0
        finally:
            self._mci("close folhabottons_probe")

    def music_path(self, name):
        """Caminho completo de uma música da lista (pasta "musica" ou, se a pasta estiver vazia, o arquivo antigo)."""
        p = os.path.join(self.music_dir, name)
        return p if os.path.isfile(p) else os.path.join(self.base, name)

    def set_click_enabled(self, enabled):
        self.click_enabled = bool(enabled)

    def set_music_volume(self, volume):
        self.music_volume = max(0, min(100, int(float(volume))))
        if self._opened:
            self._mci(f"setaudio folhabottons_music volume to {self.music_volume * 10}")

    def stop(self):
        if os.name != "nt":
            return
        self._mci("stop folhabottons_click")
        self._mci("close folhabottons_click")
        self._mci("stop folhabottons_music")
        self._mci("close folhabottons_music")
        self._opened = False
        self._click_opened = False
        self.paused = False
        self._reset_end_watch()
        self.music_enabled = True
        self.click_enabled = True
        self.music_volume = self.DEFAULT_VOLUME
