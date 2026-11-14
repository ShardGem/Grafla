# Grafos da galeria

Os arquivos desta pasta são os mesmos usados nas [capturas do Grafla](../../docs/galeria.md).
Abra pelo menu **Arquivo → Abrir** ou passe o caminho ao iniciar:

```bash
uv run grafla examples/galeria/rotas-de-entrega.grafla
```

| Arquivo | O que explorar |
| --- | --- |
| [rotas-de-entrega.grafla](rotas-de-entrega.grafla) | Dijkstra e caminhos alternativos, de **1 · CD** para **10 · Destino**. |
| [buscas-em-rede.grafla](buscas-em-rede.grafla) | Compare BFS e DFS a partir de **1 · Central**. Use a tabela ou o slider para escolher uma etapa. |
| [rede-de-fibra.grafla](rede-de-fibra.grafla) | Execute **Árvore geradora mínima** para conectar os nove pontos pelo menor custo. |
| [dependencias-do-projeto.grafla](dependencias-do-projeto.grafla) | Veja uma sequência válida de tarefas com **Ordenação topológica**. |
| [comunidades.grafla](comunidades.grafla) | Execute **Componentes conexos / fracos** e selecione um dos quatro grupos. |
| [equipe-do-projeto.grafla](equipe-do-projeto.grafla) | Edite o vértice central ou crie novas conexões. Ele está fixado para preservar sua posição durante a física. |
| [fluxo-de-pedidos.grafla](fluxo-de-pedidos.grafla) | Laços, conexões de ida e volta e rótulos de transição num fluxo de estados. |
| [matriz-de-pesos.grafla](matriz-de-pesos.grafla) | Em **Construir → Matriz**, marque **Pesos**. A conexão **1 → 2** tem custo zero. |
| [grafo-da-matriz.grafla](grafo-da-matriz.grafla) | Uma matriz simétrica que virou um grafo não direcionado, com os vértices espaçados para leitura. |
| [rede-gerada.grafla](rede-gerada.grafla) | Rede com 18 vértices e 24 arestas, gerada com seed **57** e colorida depois. |
| [rede-circular.grafla](rede-circular.grafla) | A mesma rede organizada pelo layout circular. As conexões são preservadas. |
| [fisica-em-grupos.grafla](fisica-em-grupos.grafla) | Três centros fixados e seus vizinhos, organizados com o perfil **Suave**. |
| [fisica-com-gravidade.grafla](fisica-com-gravidade.grafla) | O mesmo exemplo após ajustar a gravidade para **0,18** e a centralização para **0,003**. |
| [pessoas-e-projetos.grafla](pessoas-e-projetos.grafla) | Uma rede bipartida. Selecione **Ana**, **Bia** e **Web** com Ctrl+clique para editar o grupo. |
| [rotas-tema-claro.grafla](rotas-tema-claro.grafla) | As rotas de entrega com cores ajustadas para o fundo claro. |
| [metro-urbano.grafla](metro-urbano.grafla) | Dezessete estações e três linhas. Compare a viagem de **9 · Campus** para **15 · Porto** com Dijkstra e Caminhos simples. Os pesos representam minutos por trecho. |
| [metro-tema-claro.grafla](metro-tema-claro.grafla) | A mesma rede de metrô com uma paleta para o tema claro. |
| [pre-requisitos.grafla](pre-requisitos.grafla) | Doze disciplinas em um grafo dirigido acíclico. Execute **Ordenação topológica** para encontrar uma sequência possível de estudos. |
| [arvore-binaria.grafla](arvore-binaria.grafla) | Quinze valores em uma árvore binária. Compare BFS e DFS a partir de **1 · 50**. |
| [arquitetura-de-servicos.grafla](arquitetura-de-servicos.grafla) | Clientes, gateway, serviços, banco e fila. Inspecione as direções e os rótulos das chamadas. |
| [servicos-tema-claro.grafla](servicos-tema-claro.grafla) | A arquitetura de serviços com cores para o tema claro. Recolha os painéis para ver o diagrama inteiro. |
| [mapa-de-estudos.grafla](mapa-de-estudos.grafla) | Dezenove vértices, seis assuntos e cores por ramo. Experimente editar os tamanhos e mover um ramo inteiro. |
| [mapa-tema-claro.grafla](mapa-tema-claro.grafla) | O mapa de estudos no tema claro. Selecione os vértices **5, 6 e 7** para editar o ramo Caminhos. |
| [malha-de-rede.grafla](malha-de-rede.grafla) | Vinte e cinco vértices e quarenta conexões. O layout em grade organiza a rede; o snap ajuda nos próximos movimentos. |
| [grafo-completo-k8.grafla](grafo-completo-k8.grafla) | Oito vértices e vinte e oito arestas, com todos os pares conectados. Reorganize pelo layout circular. |
| [circuito-cultural.grafla](circuito-cultural.grafla) | Pesos fracionários e uma conexão de custo zero. Execute Dijkstra de **1 · Casa** para **5 · Café**. |

Os grafos são fictícios. Tema, seleção, resultados das análises e ajustes da física
pertencem à sessão do editor e não são salvos dentro do `.grafla`. O roteiro
[`tools/capturar_galeria.py`](../../tools/capturar_galeria.py) monta esses estados para
reproduzir as imagens.
