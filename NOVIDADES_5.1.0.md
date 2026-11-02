# Verificação de código-fonte — versão 5.1.0

## Resultado da comparação com 5.0.5

A tag `5.1.0` aponta para o commit `27586d23754978fbae86e146f577cd4043e0352d`. A tag `5.0.5` aponta para `5c989efb6dafb58bbada882848762884240706cf`.

Na comparação das árvores do Git, os arquivos Python rastreados têm os mesmos hashes nas duas tags. Os módulos verificados incluem:

- `app.py`
- `theme.py`
- `detect.py`
- `process.py`
- `layout.py`
- `groups.py`
- `audio.py`
- `cdplayer.py`
- `winprint.py`
- `ajuda.py`

Assim, não é correto atribuir à tag 5.1.0 novas funcionalidades de código que não aparecem na árvore versionada.

## O que o código rastreado implementa

- Interface Windows com Tkinter/ttk.
- Detecção de círculos com OpenCV e refinamento dos recortes.
- Agrupamento de artes semelhantes.
- Recorte circular, giro e contorno físico de 5 mm.
- Organização em folhas A4, A3 e tamanhos personalizados.
- Exportação em PDF/PNG e impressão nativa do Windows.
- Temas visuais, áudio e leitor de CD estilo Windows 95.
- Ajustes manuais, pré-visualização com zoom e cache de renderização.

## Branch de desenvolvimento

A branch `feature/salvia-editorial-criar-folha` contém alterações que não estão na tag 5.1.0:

- Nova aba **Criar Folha**, para carregar uma imagem, reposicioná-la, ajustar zoom, centralizar, adicionar à folha e salvar o botton individual em PNG.
- Temas **Sálvia Mono** e **Editorial clássico**.
- Atualizações relacionadas à implementação desses recursos em `app.py` e `theme.py`.

A comparação entre essa branch e a tag 5.0.5 mostra divergência de histórico; ela não deve ser tratada como se já estivesse incorporada à release 5.1.0.

## Divergência a conferir na publicação

A release 5.1.0 possui um ativo manual chamado `Codigo-fonte.zip` (37.514.145 bytes) e um instalador chamado `Instalador-Folha-de-Bottons-PySide6-5.1.0.exe`. O código rastreado pela tag, porém, usa Tkinter. O conteúdo binário do ZIP anexado precisa ser conferido diretamente para confirmar se ele contém a implementação mais recente e se corresponde ao instalador.

Este documento registra apenas o que foi confirmado na árvore do GitHub; não presume o conteúdo interno do ativo ZIP.