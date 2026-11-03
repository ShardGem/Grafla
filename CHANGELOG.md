# Changelog

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
