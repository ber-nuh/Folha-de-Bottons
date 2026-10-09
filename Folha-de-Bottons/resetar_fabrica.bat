@echo off
rem Restaura o Folha de Bottons ao padrao de fabrica (como na primeira vez que abre).
rem Coloque ESTE arquivo na mesma pasta do app.py (ou do FolhaDeBottons.exe) e de dois cliques.
cd /d "%~dp0"
title Folha de Bottons - padrao de fabrica
set FALHOU=

echo.
echo  RESTAURAR PADRAO DE FABRICA - Folha de Bottons
echo  ----------------------------------------------
echo  Isto apaga as configuracoes salvas:
echo    - tema, tamanho do texto e alto contraste
echo    - musica, efeito de clique, volume e leitor de musica
echo    - a introducao volta a aparecer na proxima abertura
echo    - o registro de erros e os arquivos temporarios de impressao
echo.
echo  Suas musicas (pasta musica) e efeitos (pasta efeito) NAO sao apagados.
echo.
echo  Feche o Folha de Bottons antes de continuar.
echo.
choice /c SN /n /m "Restaurar agora? (S = sim, N = cancelar): "
if errorlevel 2 goto cancelado

:checar
tasklist /fi "imagename eq FolhaDeBottons.exe" 2>nul | find /i "FolhaDeBottons.exe" >nul
if errorlevel 1 goto limpar
echo.
echo O Folha de Bottons ainda esta aberto. Feche a janela dele e continue.
echo Para cancelar, feche esta janela.
pause
goto checar

:limpar
echo.
call :apagar "config_folha_bottons.json"
call :apagar "erro_folha_bottons.log"
if exist "%TEMP%\FolhaDeBottons_impressao" (
  rmdir /s /q "%TEMP%\FolhaDeBottons_impressao"
  echo [ok] arquivos temporarios de impressao apagados
)

echo.
if defined FALHOU (
  echo Algo nao foi apagado. Feche o programa e rode este arquivo de novo.
) else (
  echo Pronto! O programa voltou ao padrao de fabrica.
  echo Na proxima abertura ele usa o Tema padrao e mostra a introducao.
)
echo.
pause
exit /b 0

:cancelado
echo.
echo Cancelado. Nada foi apagado.
pause
exit /b 0

:apagar
if not exist "%~1" (
  echo [--] %~1 : ja estava limpo
  exit /b 0
)
del /f /q "%~1" >nul 2>&1
if exist "%~1" (
  echo [ERRO] nao consegui apagar %~1
  set FALHOU=1
) else (
  echo [ok] %~1 apagado
)
exit /b 0
