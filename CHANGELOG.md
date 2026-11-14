# Changelog

## Não lançado — precisão de interação e física configurável

- Propriedades com prévia no canvas, Aplicar em uma operação de histórico e
  Cancelar sem alterar o documento. Inclui vértices, arestas e grupos; recuperação
  e arquivos guardam apenas edições confirmadas. Roda de cores com brilho e
  hexadecimal opcional, seleção que preserva a cor escolhida, X/Y na mesma linha,
  lupa em Buscar e marca sem borda de
  foco persistente. Galeria atualizada com a prévia e o seletor de cores.
- Galeria refeita com 30 capturas em 3360×2100, variações nos dois temas e 26 grafos
  para abrir no editor. Inclui metrô, árvore binária, serviços, mapa de estudos,
  pré-requisitos, malha, K8 e custos decimais. Imagens antigas substituídas,
  novo painel de destaques e capturas da busca, preferências e etapas da abertura.
- Nova marca do autor na janela e no executável, símbolo no canto superior esquerdo
  com acesso ao Sobre, splash redesenhada com progresso real e tela Sobre nos dois
  temas. Capturas e GIF atualizados para mostrar a identidade nova.
- GIF da física em funcionamento, com centros fixados, pausa e retomada após
  ajustar a distância ideal. Inclui o grafo inicial e o roteiro de geração.
- Duplo clique respeita o modo ativo; construção não seleciona nem arrasta elementos.
  Origem de aresta distinta da seleção, cancelamento explícito, laços opcionais e
  conexões em sequência. Snap deixa vértices não movidos intactos.
- Ícones com silhuetas preenchidas inspiradas no legado, estados completos e
  transições opcionais. Barra compacta mantém os controles acessíveis a 1024 px.
- Undo/Redo consolida o preview uma única vez e pausa a física até Retomar;
  patches de atributos preservam coordenadas e comandos de física só possuem x/y.
- Rótulos/estilos e ajustes ao vivo preservam a sessão e o momento da simulação.
- Aba Física com três perfis, 12 parâmetros persistentes e ajustes avançados
  recolhíveis; forças simétricas, corte suave e integração em subpassos limitados.
- Preview de posições reutiliza itens; arestas mantêm caches de rótulo, hit e bounds.
- Preferências de interação, direção e pesos padrão persistidas; inspector compacto,
  faixa de contexto e controles numéricos com setas consistentes.
- Regressões de seleção, duplo clique, Undo/Redo, física e visibilidade dos valores;
  benchmark reproduzível da simulação via `tools/benchmark.py --physics`.

## 2.1.0 — workspace e exploração contextual

- Faixa horizontal de ferramentas com ícones ativos, grupos de ações e rótulos
  que se compactam conforme o espaço disponível.
- Slider de zoom sincronizado com roda, fit, atalhos e botões, junto a grade/snap.
- Gerador, matriz e layouts integrados ao workspace; edição pendente e undo preservados.
- Rotas selecionáveis com custo e sequência; tabela lazy e slider de etapas ligados ao canvas.
- Relatório textual sob demanda; mais área de canvas durante a exploração.
- Visitas, vértice atual e caminho com estados distintos e contexto legível.
- Mudanças de algoritmo/origem/destino cancelam resultados que não correspondem à nova consulta.
- Splash com mínimo de 1,8 s, ajustável de 0,5 a 5 s, sem bloquear o event loop.
- CI instala o runtime gráfico do Qt no Linux e usa setup-uv com Node 24.

## 2.0.0 — primeira versão renovada

- Domínio sem Qt, documento único, patches reversíveis e histórico de 60 operações.
- Arquivos .grafla versionados, validação, gravação atômica, recentes e recuperação.
- Interface centralizada em temas, inspector, ferramentas vetoriais, resultados e
  busca; moldura e controles nativos de janela.
- Física acessível com estado visível, fixação de vértices, estabilização e pausa
  sem perda de posições; movimento consolidado em undo.
- Canvas orientado a eventos, mapas de incidentes e geometria incluindo as setas.
- Correção das arestas fantasmas, duplicação na matriz, custo com peso 1, geração
  incompleta e cancelamento que continuava modificando o documento.
- Análises em snapshots, limites/cancelamento de buscas caras, invalidação de
  resultados e visualização BFS/DFS com arestas percorridas e fila/pilha.
- Exportação real PNG/JPEG/SVG/PDF, seleção/transparência e copiar CSV da matriz.
- Copiar/colar subgrafos, layouts, multisseleção, pan temporário e zoom no cursor.
- Splash de bootstrap sem atraso artificial; preferências persistentes.
- Pyproject/lock, testes de domínio/integração/UI, Ruff, mypy e CI Linux/Windows.
- Um spec onedir, sem UPX, com assets e versão central; testes de startup do pacote.

O código legado recebido está preservado no commit `a9c310d` para comparação. A
licença do código do aplicativo continua a cargo do mantenedor. Não há assinatura
digital, tag ou GitHub Release criada automaticamente por esta alteração.
