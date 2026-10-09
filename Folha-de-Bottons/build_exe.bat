@echo off
rem Coloque ESTE arquivo, o icon.ico, o winprint.py, o cdplayer.py, o ajuda.py e o process.py na mesma pasta do app.py e de dois cliques.
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado no PATH.
  goto erro
)

python -m pip install --upgrade pyinstaller numpy pillow
if errorlevel 1 goto erro
python -m pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python
python -m pip install --upgrade opencv-contrib-python
if errorlevel 1 goto erro

echo.
echo Testando se o OpenCV funciona neste Python...
python -c "import cv2, numpy; print('OpenCV', cv2.__version__, 'OK')"
if errorlevel 1 goto erro

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean --windowed --onedir --name FolhaDeBottons --icon icon.ico --collect-all cv2 --hidden-import cv2 --hidden-import numpy --hidden-import audio --hidden-import cdplayer --hidden-import ajuda --hidden-import detect --hidden-import process --hidden-import layout --hidden-import groups --hidden-import theme --hidden-import winprint --hidden-import PIL.ImageWin app.py
if errorlevel 1 goto erro

if exist musica xcopy /e /i /y musica "dist\FolhaDeBottons\musica" >nul
if exist efeito xcopy /e /i /y efeito "dist\FolhaDeBottons\efeito" >nul
if exist models xcopy /e /i /y models "dist\FolhaDeBottons\models" >nul
if exist config_folha_bottons.json copy /y config_folha_bottons.json "dist\FolhaDeBottons\" >nul
if exist capzlock.mp3 copy /y capzlock.mp3 "dist\FolhaDeBottons\" >nul
copy /y icon.ico "dist\FolhaDeBottons\" >nul
if exist resetar_fabrica.bat copy /y resetar_fabrica.bat "dist\FolhaDeBottons\" >nul

echo.
echo Pronto!  dist\FolhaDeBottons\FolhaDeBottons.exe
echo Botao direito nele e "Fixar na barra de tarefas".
pause
exit /b 0

:erro
echo.
echo Algo falhou - veja a mensagem acima.
pause
exit /b 1
