"""Atalho sem console: dê dois cliques neste arquivo para abrir o programa (mesma pasta do app.py)."""
import os
import runpy

os.chdir(os.path.dirname(os.path.abspath(__file__)))
runpy.run_path("app.py", run_name="__main__")
