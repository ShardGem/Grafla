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

Os grafos são fictícios. Tema, seleção, resultados das análises e ajustes da física
pertencem à sessão do editor e não são salvos dentro do `.grafla`. O roteiro
[`tools/capturar_galeria.py`](../../tools/capturar_galeria.py) monta esses estados para
reproduzir as imagens.
