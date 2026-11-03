# Arquitetura do Grafla 2.0

## Autoridade dos dados

`domain.py` contém dataclasses de vértice, aresta e grafo, validação, geração e
layouts. Não importa Qt. IDs não são rótulos; referências de arestas usam IDs e
nenhum QGraphicsItem é serializado. Pesos não ponderados têm custo 1.

`Document` é a fronteira de mutação. Uma operação prepara uma cópia, valida e
calcula um patch dos elementos alterados. `GraphCommand` armazena somente os
vértices/arestas afetados e sequências de IDs; não retém um grafo inteiro por
comando. O QUndoStack mantém 60 operações. Edição rejeitada não toca o grafo atual.
Operações grandes ainda clonam/comparam o modelo durante sua preparação; o custo
de commit com 5.000 vértices é medido separadamente do movimento visual.

`Change` identifica elementos afetados e distingue preview de física. Alteração
estrutural/rótulos atualiza os seletores; mover um vértice não repovoa todos os
combos. Toda mudança relevante invalida resultados associados à revisão anterior.

## Apresentação

`MainWindow` compõe menus, toolbars, docks, inspector e preferências. A moldura do
SO permanece nativa. `file_actions.py` cuida do ciclo do documento, recentes e
recuperação; `analysis_controller.py` cuida de jobs, resultados e playback.

`shell.py` compõe a arquitetura visual: header, faixa horizontal de modos, canvas,
zoom e painel contextual. `workspace.py` contém gerador/matriz/layouts integrados;
`result_browser.py` apresenta rotas e um modelo lazy das etapas. Listas, tabelas e
sliders emitem apenas a escolha de índice; não executam lógica matemática.

`Canvas` mantém mapas por ID, incidentes e pares de extremos. `items.py` desenha
vértices e arestas. Deslocar um item atualiza somente as arestas incidentes;
mudanças estruturais reconciliam os mapas. Setas, labels e áreas de hit pertencem
aos bounds. Não há timer de repaint nem consulta à cena inteira por aresta.

Seleção usa o mecanismo Qt. Arrasto mostra preview dos itens e gera um comando
único no release. Operações em lote evitam uma notificação de seleção por item.
Modo, preview de conexão, seleção e destaque não alteram a topologia do documento.

Atalhos/actions ficam centralizados na construção da janela. Letras de ferramentas,
Delete e operações de subgrafo têm escopo do canvas. Inputs mantêm seu comportamento
nativo de edição. A busca permite acessar comandos e localizar vértices pelo teclado.

## Física

`physics.py` é um passo matemático puro: repulsão espacial local com orçamento de
vizinhos, atração por arestas, amortecimento e limite de velocidade/deslocamento.
Nós fixados participam como obstáculos, mas não são movidos. Nós coincidentes têm
separação determinística. Coordenadas respeitam os limites do domínio.

`PhysicsController` tem timer de 30 ms **somente durante o movimento**. Ao desligar,
estabilizar por 12 passos ou completar 500 iterações, ele para e transforma as
posições finais numa operação desfazível. A opção pode continuar habilitada em
repouso, sendo reativada por uma edição. Desativar e reativar limpa velocidades,
sem restaurar posições antigas.

Antes de edição manual, save ou fechamento, a simulação é pausada e seu preview
é consolidado. Campos de posição ficam desabilitados durante movimento; editar
um rótulo não reaplica coordenadas antigas do inspector.

## Algoritmos e concorrência

`algorithms.py` valida o snapshot e adapta para NetworkX. A UI não conhece objetos
do backend. Uma aresta não direcionada vira dois arcos com o mesmo ID; contratos
específicos impedem usar MST em grafos mistos/direcionados e topológica em ciclos.

`AnalysisTask` roda no QThreadPool e devolve dados por sinais; somente a thread da
UI modifica widgets. Isso dá responsividade, não aceleração garantida para Python
CPU-bound. Buscas exponenciais usam DFS iterativa com limite de caminhos e relógio
verificado dentro da exploração, inclusive sem resultados intermediários. Cancelar
usa threading.Event. Token e revisão impedem aplicar resposta obsoleta.

BFS/DFS retornam eventos de visita, arestas de descoberta e fila/pilha limitada a
30 entradas exibidas por passo. Playback tem um timer ativo apenas em reprodução;
voltar utiliza os eventos guardados. Não há snapshot completo do grafo por passo.

## Arquivos e inicialização

`.grafla` tem `format`, `schema_version` e dados puros. Decode rejeita versão
incompatível, IDs duplicados, extremos ausentes, tipos inválidos e números não
finitos antes de substituir o documento. QSaveFile faz gravação atômica. O estado
clean só é atualizado após commit do arquivo.

QSettings mantém preferências, recentes e geometria. Recuperação tem arquivo próprio
e abre como documento novo/dirty. Exportadores usam QPainter/QImage/QSvgGenerator/
QPdfWriter; ocultam temporariamente decoração e itens fora da seleção e restauram
o editor também quando ocorre falha.

`app.py` cria QApplication e logging, apresenta splash, agenda etapas reais de tema
e editor pelo event loop e mostra a janela pronta. A preferência de duração mínima
(1,8 s por padrão) é atendida por um timer preciso, contado desde o showEvent.
Se o carregamento já consumiu esse tempo, a janela abre imediatamente. Não há sleep.

## Testes e distribuição

Testes unitários usam o domínio sem UI; integração verifica comandos/arquivos;
pytest-qt simula operações do editor. `--smoke-test` valida o entrypoint real.
As métricas ficam em `benchmark-linux.jsonl` e o método em `tools/benchmark.py`.

A fonte única da versão é `grafla.__version__`: setuptools, splash, Sobre e recurso
Windows a leem. Um spec onedir atende cada SO no próprio SO. A CI Windows valida
o executável com backend nativo; composição real de janelas, leitores de tela e
matriz física de monitores/DPI ainda precisam de validação específica.
