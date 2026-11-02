# Folha de Bottons

Aplicativo para Windows para detectar artes circulares de bottons, agrupar modelos, organizar quantidades e preparar folhas para impressão.

**Versão publicada:** [5.1.0](https://github.com/ber-nuh/Folha-de-Bottons/releases/tag/5.1.0)  
**Downloads:** [todas as versões](https://github.com/ber-nuh/Folha-de-Bottons/releases)

## Recursos presentes no código-fonte rastreado

- Detecção de bottons circulares em imagens usando OpenCV.
- Agrupamento de artes semelhantes e controle de quantidade por modelo.
- Recorte circular e aplicação de contorno de 5 mm.
- Montagem de folhas A4, A3 ou em tamanho personalizado.
- Ajuste manual de bottons detectados, seleção pela prévia e navegação pela folha.
- Exportação de folhas em PDF e PNG com DPI configurável.
- Impressão em tamanho real pelo diálogo nativo do Windows.
- Temas visuais, acessibilidade, áudio e leitor estilo CD Player no tema Windows 95 clássico.

## Código-fonte e versões: atenção à correspondência

A tag `5.1.0` atualmente aponta para o commit `27586d23754978fbae86e146f577cd4043e0352d`. Ao comparar essa tag com `5.0.5`, os arquivos Python rastreados têm os mesmos conteúdos (mesmos hashes). Portanto, o código-fonte versionado na tag 5.1.0 não demonstra alterações de implementação em relação à 5.0.5.

O código-fonte rastreado nessa tag utiliza **Python com Tkinter**, além de OpenCV, NumPy e Pillow. O nome do instalador anexado à release 5.1.0 contém “PySide6”; essa diferença de identificação precisa ser conferida com o conteúdo do arquivo `Codigo-fonte.zip` anexado à release antes de afirmar que o instalador e o código versionado correspondem à mesma implementação.

Existe também a branch de desenvolvimento [`feature/salvia-editorial-criar-folha`](https://github.com/ber-nuh/Folha-de-Bottons/tree/feature/salvia-editorial-criar-folha), que contém alterações adicionais, incluindo a aba **Criar Folha** e os temas **Sálvia Mono** e **Editorial clássico**. Essa branch não está incorporada à tag 5.1.0.

## Executar pelo código-fonte rastreado

Requisitos: Windows e Python compatível com as dependências listadas em `Folha-de-Bottons/requirements.txt`.

1. Abra o Prompt de Comando na pasta `Folha-de-Bottons`.
2. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

3. Inicie o programa:

```powershell
python app.py
```

Também é possível executar `abrir_folha_de_bottons.pyw` com duplo clique.

## Impressão

Ao imprimir, selecione **100% / Tamanho real** para evitar que a escala da página altere as medidas dos bottons.

## Downloads e segurança

Baixe instaladores somente pela página oficial de [Releases](https://github.com/ber-nuh/Folha-de-Bottons/releases). Confira o nome e a versão do arquivo. Não desative o antivírus ou a proteção do Windows para instalar o programa.

---

Projeto idealizado por **Ber-nuh** e desenvolvido com auxílio de inteligência artificial.