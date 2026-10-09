"""Impressão pelo diálogo nativo do Windows (PrintDlg).

Abre a janela padrão de impressão, com o botão "Preferências/Propriedades" do próprio driver da impressora
(tipo de papel, qualidade, cor, sem bordas...). As configurações escolhidas valem para o trabalho, e as páginas
são desenhadas no tamanho real em milímetros (100%), sem depender de leitor de PDF.
Só usa ctypes + Pillow (PIL.ImageWin): nada para instalar.
"""
import ctypes
from ctypes import wintypes as wt

from PIL import Image, ImageWin


class PrintCancelled(Exception):
    """O usuário fechou o diálogo de impressão."""


_PACK = 1 if ctypes.sizeof(ctypes.c_void_p) == 4 else 8   # o Windows empacota PRINTDLG em 1 byte só no 32 bits


class PRINTDLGW(ctypes.Structure):
    _pack_ = _PACK
    _fields_ = [("lStructSize", wt.DWORD), ("hwndOwner", wt.HWND), ("hDevMode", wt.HGLOBAL),
                ("hDevNames", wt.HGLOBAL), ("hDC", wt.HDC), ("Flags", wt.DWORD),
                ("nFromPage", wt.WORD), ("nToPage", wt.WORD), ("nMinPage", wt.WORD), ("nMaxPage", wt.WORD),
                ("nCopies", wt.WORD), ("hInstance", wt.HINSTANCE), ("lCustData", wt.LPARAM),
                ("lpfnPrintHook", ctypes.c_void_p), ("lpfnSetupHook", ctypes.c_void_p),
                ("lpPrintTemplateName", wt.LPCWSTR), ("lpSetupTemplateName", wt.LPCWSTR),
                ("hPrintTemplate", wt.HGLOBAL), ("hSetupTemplate", wt.HGLOBAL)]


class DOCINFOW(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int), ("lpszDocName", wt.LPCWSTR), ("lpszOutput", wt.LPCWSTR),
                ("lpszDatatype", wt.LPCWSTR), ("fwType", wt.DWORD)]


PD_NOSELECTION, PD_NOPAGENUMS, PD_RETURNDC, PD_USEDEVMODECOPIESANDCOLLATE = 0x4, 0x8, 0x100, 0x40000
HORZRES, VERTRES, LOGPIXELSX, LOGPIXELSY = 8, 10, 88, 90
PHYSICALWIDTH, PHYSICALHEIGHT, PHYSICALOFFSETX, PHYSICALOFFSETY = 110, 111, 112, 113


def _flatten(p):
    """RGBA -> RGB sobre branco (impressora não tem transparência)."""
    base = Image.new("RGB", p.size, (255, 255, 255))
    if p.mode == "RGBA":
        base.paste(p, mask=p.getchannel("A"))
        return base
    return p.convert("RGB")


def print_pages(pages, w_mm, h_mm, hwnd=0, state=None, name="Folha de Bottons", confirm=None):
    """Mostra o diálogo de impressão e imprime 'pages' (imagens PIL de w_mm x h_mm) no tamanho real.

    state:   dict que guarda as escolhas (impressora, papel, qualidade) para a próxima vez, enquanto o programa estiver aberto.
    confirm: função(texto) -> bool, chamada se a folha for maior que o papel escolhido (será cortada).
    Levanta PrintCancelled se o usuário cancelar."""
    state = state if state is not None else {}
    comdlg, gdi = ctypes.WinDLL("comdlg32", use_last_error=True), ctypes.WinDLL("gdi32", use_last_error=True)
    comdlg.PrintDlgW.argtypes, comdlg.PrintDlgW.restype = [ctypes.POINTER(PRINTDLGW)], wt.BOOL
    comdlg.CommDlgExtendedError.restype = wt.DWORD
    gdi.GetDeviceCaps.argtypes, gdi.GetDeviceCaps.restype = [wt.HDC, ctypes.c_int], ctypes.c_int
    gdi.StartDocW.argtypes, gdi.StartDocW.restype = [wt.HDC, ctypes.POINTER(DOCINFOW)], ctypes.c_int
    for fn in ("StartPage", "EndPage", "EndDoc", "AbortDoc", "DeleteDC"):
        f = getattr(gdi, fn)
        f.argtypes, f.restype = [wt.HDC], ctypes.c_int

    pd = PRINTDLGW()
    pd.lStructSize = ctypes.sizeof(PRINTDLGW)
    pd.hwndOwner = hwnd
    pd.hDevMode, pd.hDevNames = state.get("devmode"), state.get("devnames")   # lembra a impressora/configurações
    pd.Flags = PD_RETURNDC | PD_NOSELECTION | PD_NOPAGENUMS | PD_USEDEVMODECOPIESANDCOLLATE
    pd.nCopies = pd.nMinPage = pd.nMaxPage = pd.nFromPage = pd.nToPage = 1
    ok = comdlg.PrintDlgW(ctypes.byref(pd))
    state["devmode"], state["devnames"] = pd.hDevMode, pd.hDevNames
    if not ok:
        err = comdlg.CommDlgExtendedError()
        if err:
            raise OSError(f"O diálogo de impressão falhou (código {err}).")
        raise PrintCancelled()

    hdc = pd.hDC
    try:
        copies = max(1, int(pd.nCopies))   # 1 quando o driver cuida das cópias (via configurações da impressora)
        dx, dy = gdi.GetDeviceCaps(hdc, LOGPIXELSX), gdi.GetDeviceCaps(hdc, LOGPIXELSY)
        pw, ph = gdi.GetDeviceCaps(hdc, PHYSICALWIDTH), gdi.GetDeviceCaps(hdc, PHYSICALHEIGHT)
        ox, oy = gdi.GetDeviceCaps(hdc, PHYSICALOFFSETX), gdi.GetDeviceCaps(hdc, PHYSICALOFFSETY)
        # papel em paisagem e folha em retrato (ou o contrário): gira a folha
        turn = (pw > ph) != (w_mm > h_mm)
        wm, hm = (h_mm, w_mm) if turn else (w_mm, h_mm)
        tw, th = round(wm / 25.4 * dx), round(hm / 25.4 * dy)
        if (tw > pw * 1.02 or th > ph * 1.02) and confirm and not confirm(
                "A folha é maior que o papel escolhido na impressora e será cortada.\n\nImprimir mesmo assim?"):
            raise PrintCancelled()
        x0, y0 = max(0, (pw - tw) // 2) - ox, max(0, (ph - th) // 2) - oy   # origem do GDI = início da área imprimível

        di = DOCINFOW(ctypes.sizeof(DOCINFOW), name, None, None, 0)
        if gdi.StartDocW(hdc, ctypes.byref(di)) <= 0:
            raise OSError("Não foi possível iniciar a impressão (a impressora está disponível?).")
        try:
            for _ in range(copies):
                for p in pages:
                    img = _flatten(p)
                    if turn:
                        img = img.rotate(90, expand=True)
                    if gdi.StartPage(hdc) <= 0:
                        raise OSError("A impressora recusou a página.")
                    ImageWin.Dib(img).draw(int(hdc), (x0, y0, x0 + tw, y0 + th))
                    gdi.EndPage(hdc)
            gdi.EndDoc(hdc)
        except BaseException:
            gdi.AbortDoc(hdc)
            raise
    finally:
        gdi.DeleteDC(hdc)
