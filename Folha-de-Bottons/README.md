# Folha de Bottons

Aplicativo para Windows para detectar artes circulares de bottons, organizar as quantidades em folhas e exportar/imprimir em tamanho real.

**Idealizado por Ber-nuh e feito inteiramente pela IA.**

## Recursos

- Detecção e recorte de artes circulares.
- Agrupamento de artes semelhantes e escolha de quantidades.
- Montagem de folhas A4, A3 ou tamanho personalizado.
- Exportação para PDF/PNG e impressão.
- Temas visuais e opções de acessibilidade.

## Executar pelo código-fonte

Requisitos: Windows e Python compatível com as dependências abaixo.

1. Abra o Prompt de Comando nesta pasta.
2. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

3. Inicie o programa:

```powershell
python app.py
```

Ou dê duplo clique em `abrir_folha_de_bottons.pyw` para abrir sem console.

## Gerar o executável

Com Python instalado no Windows, dê duplo clique em `build_exe.bat`. O script instala/atualiza as dependências e gera `dist\FolhaDeBottons\FolhaDeBottons.exe`.

## Arquivos de áudio e modelos opcionais

As pastas `musica/`, `efeito/` e `models/` não estão neste pacote de código. O programa pode funcionar sem os arquivos de áudio opcionais. Para recursos que dependam de modelos de super-resolução, consulte `download_models.py` e confira as licenças dos modelos antes de redistribuí-los.

## Atualizações

O repositório pode ser usado para publicar o código-fonte e, posteriormente, anexar o instalador nas **GitHub Releases**. O verificador de atualizações dentro do programa ainda precisa ser implementado e testado antes de prometer notificações automáticas aos usuários.

## Licença

Nenhum arquivo de licença foi adicionado automaticamente. Até que uma licença seja escolhida, todos os direitos autorais permanecem reservados; a publicação pública do código não concede, por si só, permissão para reutilizá-lo ou redistribuí-lo.
