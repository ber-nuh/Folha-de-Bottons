# Otimizações — Folha de Bottons

Foram revisados os módulos Python do projeto, com foco em detecção, processamento de imagem, agrupamento e cache.

## Alterações

1. **Detecção de círculos — refinamento duplicado removido**
   - `detect.py`
   - Cada botton estava passando por `_refine()` duas vezes consecutivas.
   - Isso repetia blur gaussiano, remapeamento, gradientes e ajuste do círculo.
   - Agora há apenas uma chamada.

2. **Componentes conectados — processamento por bounding box**
   - `detect.py`
   - Antes, para cada componente encontrado, era criada uma máscara do tamanho da folha inteira (`lab == i`).
   - Agora cada componente é processado somente dentro do seu bounding box.
   - O ganho cresce bastante em folhas com muitos componentes/detalhes.

3. **Cache de máscaras circulares**
   - `process.py`
   - As máscaras antialiasadas usadas em `make_button()` são reutilizadas quando possuem o mesmo tamanho.
   - O cache tem limite de 64 tamanhos para evitar crescimento indefinido.

4. **Cache de assinaturas para agrupamento**
   - `app.py`
   - A assinatura visual usada para descobrir bottons iguais agora é calculada uma vez por geometria/origem.
   - Alterar apenas a tolerância não força o recálculo das assinaturas.
   - O cache é invalidado junto com o cache de bottons quando as fontes são limpas/recarregadas.

## Validação

- `test_synth.py`: 7/7 bottons detectados.
- `test_sizes.py`: 6/6 bottons detectados; testes de corte de margem preservados.
- `python -m compileall -q .`: sem erros de sintaxe.

## Benchmark de detecção

Em uma folha sintética de 4000×3000 com 18 bottons:

- versão original: ~0,268 s por detecção
- versão otimizada: ~0,207 s por detecção

Isso representa aproximadamente **23% de redução no tempo** nesse cenário.

Em um teste isolado com 150 componentes conectados, a etapa `_from_mask()` caiu de aproximadamente **0,576 s para 0,037 s** (cerca de **94% menos tempo**), mostrando o ganho especialmente importante em imagens com muitos componentes.
