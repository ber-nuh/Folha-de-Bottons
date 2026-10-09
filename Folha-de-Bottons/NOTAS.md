# Folha de Bottons — notas do projeto

Leia este arquivo primeiro (pessoa ou IA). Última atualização: 08/10/2026.

## O que o programa faz

Você dá uma imagem (PNG, JPG ou WEBP) com várias artes redondas de bottons/pins. O programa:

1. **detecta** cada botton redondo na imagem;
2. **agrupa** os parecidos em "tipos" e deixa você escolher a quantidade de cada tipo;
3. **recorta** cada arte em círculo e acrescenta o contorno de 5 mm (a parte que dobra por trás do pin);
4. **organiza** tudo em uma folha (A4, A3 ou tamanho personalizado) com espaçamento em mm;
5. **exporta** em PDF/PNG com DPI real, ou **imprime** em tamanho real (100%).

Tamanhos: a arte tem 32 ou 58 mm; com o contorno o botton inteiro mede 42 ou 68 mm. Esse tamanho total é o que ocupa espaço na folha.

## Ambiente

- **Só Windows** (usa winmm para áudio, PrintDlg/GDI para imprimir e DWM para a moldura da janela).
- Python 3.14 (o log mostra `Python314`). Bibliotecas: `numpy`, `pillow`, `opencv-contrib-python` (precisa ser o *contrib*, por causa do `dnn_superres`), `pyinstaller` (só para gerar o .exe).
- Interface: Tkinter/ttk (tema "clam" com cores próprias). Sem pygame, sem PyQt.

## Como rodar

| Jeito | Como |
|---|---|
| Código-fonte | `python app.py` (reabre sozinho com `pythonw`, sem console). Para depurar com console: `python app.py --console` |
| Sem console | duplo clique em `abrir_folha_de_bottons.pyw` |
| Executável | rode `build_exe.bat` → `dist\FolhaDeBottons\FolhaDeBottons.exe` (PyInstaller `--onedir`) |

Erros vão para `erro_folha_bottons.log` (ao lado do programa), porque sem console eles não aparecem em lugar nenhum.

## Mapa dos arquivos

| Arquivo | Papel |
|---|---|
| `app.py` | Interface e fluxo geral (classe `App`, ~1.800 linhas). Abas: **Bottons**, **Quantidades**, **Configurações**, **Ajuda**. Prévia com zoom/arrastar, exportar, imprimir, conta-gotas, ajuste manual do recorte. |
| `detect.py` | Detecção de círculos: segmenta o fundo (distância de cor à borda + Otsu), separa bottons encostados (transformada de distância), Hough só como plano B; `_refine` ajusta o círculo à borda real. |
| `process.py` | `open_sheet` (abre a folha), `art_circle`/`make_button` (recorte, giro, contorno de 5 mm), `edge_color` (cor do contorno por k-means), `trim_margin` (corta margem branca), ampliação (`upscale`: suave, alta, IA). |
| `groups.py` | Assinatura 32×32 da arte de cada botton; `cluster` junta os parecidos (tolerância `TOL = 20`, ajustável de 8 a 45 na aba Quantidades). |
| `layout.py` | Grade na folha (`positions`, `grid_size`), montagem das páginas e exportação PNG/PDF. Margens: 5 mm (centralizado), mínimo 3 mm por lado (canto superior esquerdo). |
| `winprint.py` | Impressão pelo diálogo nativo do Windows (`PrintDlg`) com `ctypes` + `PIL.ImageWin`. |
| `theme.py` | Temas, cores, fontes, moldura da janela (DWM), efeito vidro, alto contraste, tamanho do texto. |
| `audio.py` | Música de fundo e cliques via MCI (winmm). Pastas `musica/` e `efeito/` ao lado do programa. |
| `cdplayer.py` | Leitor de MP3 estilo "CD Player" do Windows 95 (só aparece no tema Windows 95 clássico). |
| `ajuda.py` | Textos da aba Ajuda, dicas (tooltips) e a introdução da primeira vez (`Intro`). |
| `config_folha_bottons.json` | Configurações salvas (tema, áudio, texto, contraste...). A chave `ui_arredondada` não é usada por nenhum código. |
| `build_exe.bat`, `FolhaDeBottons.spec` | Geração do .exe. Os dois precisam listar os mesmos módulos em `hiddenimport`. |
| `download_models.py` | Baixa modelos de super-resolução `.pb` para `models/`. |
| `build_template.py`, `test_sizes.py`, `test_synth.py` | Experimentos/testes soltos, **não** fazem parte do programa. Os testes gravam em `/tmp` (não existe no Windows: ajuste antes de rodar). |

A ampliação por IA/"alta qualidade" existe em `process.py` (`UP_MODES`), mas o `app.py` hoje chama `make_button` sem esse parâmetro: **não está ligada na interface**.

## Fluxo interno (para achar onde mexer)

`App.open` → `_append_source_records` → `_load_source` (`open_sheet` + `detect_circles`) → `mk` (cria o item; com "Cortar margem" ligado chama `trim_margin`, e `auto_color`) → `assign`/`regroup` (grupos) → `refresh` (prévia) → `_button` (renderiza cada botton uma vez, com cache) → `layout.build_pages` → `export` / `print_sheet`.

## Temas e o efeito vidro (decisões já tomadas)

- Temas: Windows 11 escuro (padrão), Claro moderno, Âmbar premium, Verde esmeralda, Azul profundo transparente, Windows 95 clássico. Cada um é um dicionário em `THEMES` (campos explicados no comentário no topo de `theme.py`).
- **Efeito vidro = translucidez da janela inteira**, controlada por `WINDOW_ALPHA` de cada tema (Verde esmeralda e Azul profundo 0,90; Windows 11 escuro 0,94; Claro moderno 0,96; os demais 1,0). Abaixo de ~0,85 o texto fica difícil de ler. Alto contraste força 1,0.
- **Vidro na barra de título (Mica/Acrylic) foi abandonado.** Os temas usam `WINDOW_EFFECT=None` e `WINDOW_CAPTION="solid"` (barra na cor `TITLEBAR`).
- **Nunca** combine `-alpha` com Mica/Acrylic (`DWMWA_SYSTEMBACKDROP_TYPE`) nem estenda o vidro para dentro da janela (`DwmExtendFrameIntoClientArea` com margens): o Tkinter desenha com GDI, e GDI sobre vidro fica transparente. O resultado é a janela inteira branca.
- A moldura é reaplicada ~120 ms depois da janela aparecer (`_apply_effect_soon`), porque na abertura a janela do Windows ainda não existe.
- Não há desfoque atrás da janela (blur): seria preciso `SetWindowCompositionAttribute`, não testado e com risco de deixar a janela branca.

## Folhas gigantes (corrigido em 08/10/2026)

O log mostrava `DecompressionBombError`: uma folha de 759 milhões de pixels (~27.500 × 27.500) era barrada pelo Pillow.

- `process.open_sheet` abre a folha sem o limite anti-bomba (só durante a abertura) e **reduz por média de blocos** quando passa de `MAX_SHEET_PIXELS = 100_000_000` (~10.000 × 10.000). Aquela folha vira ~84 milhões de pixels (÷3). Folhas menores ficam **idênticas** ao que eram.
- JPEG grande é decodificado direto em tamanho menor (rápido). PNG precisa ser decodificado inteiro: ~2,3 GB de RAM para 759 MP em RGB (~5 GB se tiver transparência) e pode levar um bom tempo. O cursor vira ampulheta enquanto isso.
- O programa avisa, em uma janela, que a folha foi reduzida e para qual tamanho. Falta de memória mostra uma mensagem amigável em vez de erro.
- Um botton de 42 mm a 300 DPI usa só ~500 px; mesmo reduzida, a arte de cada botton costuma ter bem mais que isso. Se quiser mais detalhe e tiver RAM, aumente `MAX_SHEET_PIXELS`.
- Três funções olhavam a folha **inteira** a cada botton (`detect._refine`, `process.trim_margin`, `process.edge_color`); agora olham só a região do botton. Resultado idêntico ao anterior (conferido pixel a pixel em folhas sintéticas, inclusive com bottons cortados pela borda da imagem); a detecção ficou ~10× mais rápida (6,4 s → 0,7 s numa folha de 25 MP).
- Ainda custa tempo por botton: `edge_color` (k-means no anel da arte) cresce com o tamanho do botton, não da folha.

## DPI da prévia

- A prévia na tela (zoom 100%) é sempre renderizada em **`PREVIEW_DPI = 120`** (constante no topo do `app.py`). A exportação e a impressão usam o DPI escolhido na interface (300 ou 600).
- Até 08/10/2026 o ajuste manual (`adj` → `_refresh_adjustment`: setas de mover/girar) refazia a página em **45 DPI** (80 no caso sem prévia) e não voltava para 120, então a imagem ficava borrada depois de qualquer ajuste. Agora usa `PREVIEW_DPI`. Custo medido: ~50 ms por ajuste, igual ao de 45 DPI, porque só o botton ajustado é refeito e o resto vem do cache.
- Com zoom acima de 100%, `sched_hi` renderiza 150 ou 300 DPI sob demanda (não mexer).

## Problemas conhecidos / ideias

- Ampliação por IA não está na interface (ver acima).
- `erro_folha_bottons.log` só cresce; as entradas de 08/10/2026 12:35–12:49 são do erro da folha gigante já corrigido.
- O atalho `FolhaDeBottons - Atalho.lnk` aponta para um caminho absoluto do PC de origem.
- Nada aqui foi testado no Windows pelo assistente que fez as últimas mudanças (só a lógica, em Linux, com Tkinter simulado): confira o visual do vidro e a abertura de uma folha grande de verdade.

## Para enviar o projeto a uma IA

- **Inclua:** todos os `.py` e `.pyw`, este `NOTAS.md`, `build_exe.bat`, `FolhaDeBottons.spec`, `config_folha_bottons.json` e o `erro_folha_bottons.log`.
- **Deixe de fora:** `build/`, `dist/`, `__pycache__/`, `models/`, `musica/`, `efeito/`, `.exe`, `.mp3`, o `.lnk` e zips antigos. Só pesam (o zip completo passa de 290 MB; o código tem ~200 KB).
- Mantenha **uma única** versão do `app.py` (já apareceram `app_multifolhas.py` e `app_corrigido_multifolhas.py` nos logs) e diga à IA qual é.
- Mande prints quando o problema for visual: a IA lê o código, mas não vê a janela nem roda o programa no Windows.


## Seleção direta pela folha
- Clicar diretamente em um botton na prévia agora seleciona o botton correspondente na lista “Bottons detectados”.
- Funciona com zoom e pan.
- Arrastar a folha continua sendo pan e não altera a seleção.
- Em páginas com bottons repetidos, clicar em qualquer repetição seleciona o item/arte correspondente na lista.
