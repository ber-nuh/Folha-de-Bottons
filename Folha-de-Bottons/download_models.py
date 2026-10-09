"""Baixa os modelos de super-resolução (.pb) para a pasta 'models' ao lado do programa.
Uso: python download_models.py"""
import os
import urllib.request

DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
BASE = {
    "EDSR": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/{}",
    "FSRCNN": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/{}",
    "ESPCN": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/{}",
}
FILES = ["FSRCNN_x2.pb", "FSRCNN_x4.pb", "ESPCN_x2.pb", "ESPCN_x4.pb", "EDSR_x2.pb", "EDSR_x4.pb"]  # leves -> pesados

os.makedirs(DEST, exist_ok=True)
for fn in FILES:
    path = os.path.join(DEST, fn)
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        print("já existe:", fn)
        continue
    url = BASE[fn.split("_")[0]].format(fn)
    try:
        print("baixando", fn, "...", end=" ", flush=True)
        urllib.request.urlretrieve(url, path)
        print(f"ok ({os.path.getsize(path) / 1e6:.1f} MB)")
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        print("falhou:", e)
print("\nModelos em:", DEST)
