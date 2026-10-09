# Folha de Bottons

Aplicativo para Windows que ajuda a detectar, organizar, dimensionar e imprimir folhas de bottons a partir de imagens. Projeto criado por **Ber-nuh**.

## Abas do programa

### Bottons
- Selecionar uma ou várias imagens/folhas para detectar os bottons.
- Detectar e recortar os bottons, com opção de remover margens brancas.
- Escolher o tamanho do botton: **32 mm de arte / 42 mm total** ou **58 mm de arte / 68 mm total**.
- Ajustar o espaçamento entre bottons e as dimensões da folha (por exemplo, A4).
- Definir o posicionamento na folha: centralizado ou no canto superior, além de visualizar a disposição e a quantidade que cabe por página.
- Exportar ou imprimir as folhas preparadas. Quando necessário, o programa divide o trabalho em várias páginas.

### Quantidades
- Agrupar imagens de bottons semelhantes por tipo.
- Definir quantas unidades de cada tipo serão incluídas.
- Ajustar a tolerância de agrupamento e reagrupar quando necessário.
- Distribuir automaticamente as quantidades em uma ou mais páginas.

### Configurações
- Selecionar o tema visual e ajustar o tamanho do texto.
- Ativar ou desativar o alto contraste para melhorar a legibilidade.
- Configurar música de fundo, volume e sons de clique.
- Verificar atualizações do programa.
- Consultar a assinatura do projeto: **Criado por Ber-nuh**.

### Ajuda
- Acessar orientações e dicas para utilizar as funções do aplicativo.

## Temas visuais

O programa inclui seis temas, que podem ser trocados nas **Configurações**:

1. **Tema padrão** — interface escura em grafite com detalhes azul-claro.
2. **Claro moderno** — interface clara, limpa, com detalhes em azul.
3. **Âmbar premium** — painel claro com detalhes âmbar/laranja e barra superior escura.
4. **Verde esmeralda** — interface escura com destaques verdes.
5. **Azul profundo transparente** — tons de azul escuro com detalhes azuis e transparência sutil.
6. **Windows 95 clássico** — aparência retrô inspirada no Windows 95, incluindo controles clássicos e um leitor de música no estilo CD Player.

Além dos temas, é possível escolher entre quatro tamanhos de texto (**Normal 100%**, **Grande 125%**, **Muito grande 150%** e **Gigante 175%**) e ativar o **alto contraste**. Essas opções ajudam a adaptar a interface à preferência e à legibilidade de cada pessoa.

## Impressão e tamanho

Para manter as medidas corretas, ao imprimir selecione **100% / Tamanho real** no diálogo de impressão, evitando opções como “Ajustar à página”, que podem alterar as dimensões dos bottons.

## Atualizações

O aplicativo pode verificar se existe uma versão mais recente publicada nas Releases do repositório. Se houver atualização, ele oferece a opção de abrir/baixar o instalador; a instalação não é executada automaticamente. Também é possível iniciar a verificação manualmente em **Configurações → Verificar atualizações**. A verificação depende de conexão com a internet.

## Gerar o instalador

O pacote inclui `gerar_instalador.bat`, que examina os arquivos da pasta atual e gera um script `.iss` para o Inno Setup. Abra o arquivo `.iss` gerado no Inno Setup, confira os caminhos e compile o instalador. Para distribuir uma versão independente, use a pasta que contém o executável final e todos os recursos necessários. Se a pasta tiver apenas arquivos `.py`/`.pyw`, o computador de destino precisará do Python e das dependências correspondentes.

## Observação

O gerador de instalador não deve incluir históricos, configurações pessoais ou arquivos temporários do computador de desenvolvimento. Faça testes de instalação e atualização antes de publicar uma nova versão.
