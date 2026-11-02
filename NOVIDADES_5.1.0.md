# Novidades — Folha de Bottons 5.1.0

Este registro foi preparado a partir do arquivo de novidades e dos módulos presentes no código-fonte 5.1.0.

## Criação de bottons

- A opção **Criar Botton > Cor de fundo…** agora funciona com imagens PNG, JPG, WEBP e SVG, inclusive quando a imagem original não possui transparência.
- A cor selecionada preenche as áreas transparentes e as sobras que aparecem quando o conteúdo é visualizado com zoom abaixo de 100%.

## Interação e organização da folha

- A roda do mouse só altera caixas de seleção, campos numéricos e controles deslizantes depois que o usuário clica no respectivo controle. Antes disso, ela continua rolando o painel.
- O zoom do círculo na aba Criar também exige clique antes de responder à roda do mouse.
- **Canto superior** passa a ser a posição padrão para projetos novos; projetos já salvos mantêm sua posição anterior.
- Duplo clique ou botão direito sobre um botton na folha abre as opções **Duplicar** e **Remover**.
- Duplicar acrescenta uma cópia e atualiza a quantidade daquele modelo.
- Remover reduz a quantidade; ao remover a última cópia, o modelo deixa a folha, mas permanece na lista.
- A ação de remoção pode ser desfeita com **Ctrl+Z**.

## Interface e acessibilidade

- Textos de janelas padrão do Qt — como seletor de cor, abrir/salvar, confirmações e copiar/colar — passam a aparecer em português.
- O tour guiado e a Ajuda (F1) foram atualizados para refletir as funções recentes.
- Foi adicionado o tema **Escuro**, com cinza neutro e detalhes em violeta.

## Temas clássicos

- O tema **Windows 95 clássico** recebeu elementos inspirados no 98.css: relevos, caixas, setas, barra de título em degradê, fonte e cores clássicas.
- No tema Windows 95, elementos da barra do visor, etiquetas numéricas, seletor de imagem e amostras de cor receberam acabamento quadrado.
- Os elementos do pacote de ícones clássicos são utilizados somente nesse tema.

## Notificações

- Avisos de exportação, impressão, detecção, projetos e atualização passaram a ser exibidos como notificações temporárias no canto inferior direito.
- As notificações exibem o ícone do programa, título e mensagem; desaparecem automaticamente, podem ser fechadas por clique e ficam pausadas enquanto o cursor está sobre elas.
- Notificações simultâneas são empilhadas.
- O estilo das notificações acompanha o tema ativo. No Windows 95, elas adotam uma janela cinza com relevo 3D e barra de título azul-marinho.
- Erros graves e perguntas que exigem resposta continuam sendo apresentados em janelas de diálogo.

---

**Versão identificada no código-fonte:** 5.1.0  
**Interface:** Python / PySide6
