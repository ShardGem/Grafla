# Revisão da experiência do workspace

## Diagnóstico antes da alteração

A versão 2.0 separou domínio, documento, canvas e execução, mas sua composição
visual ainda fragmentava o trabalho: toolbar vertical larga, toolbar global
separada, inspector com controles altos e um dock de texto que tomava a parte
inferior do grafo assim que uma análise terminava. O usuário precisava ler uma
lista textual e usar Anterior/Próxima para escolher uma rota. Gerar/importar matriz
ainda abria janelas próprias. Zoom não tinha uma escala contínua visível.

O problema está na apresentação e no fluxo, não nos contratos matemáticos. Domínio,
serialização, algoritmos e física serão preservados. A janela continua nativa.

## Decisões

- Faixa horizontal de ferramentas com agrupamentos, ícone ativo distinto, cor e
  estado checked; os modos usam apenas ícones quando as fontes ou a largura
  deixam menos espaço. As letras de atalho continuam restritas ao canvas.
- Header de documento com ações globais compactas; mais largura e altura para o
  grafo, sem abrir o relatório textual automaticamente.
- Controle de zoom contínuo/logarítmico, botões ±, 100% e ajustar, com sincronização
  bidirecional entre slider, roda, fit e atalhos.
- Análise organizada em entrada → resumo → rotas/etapas → playback. Escolher uma
  rota ou etapa na lista destaca o conteúdo correspondente no grafo. Custos,
  sequência, execução parcial e fila/pilha ficam associados ao resultado.
- Gerador, matriz e layouts dentro do painel Construir. A edição pendente não
  altera o documento até Aplicar; uma aplicação continua sendo um único undo.
- Relatório completo permanece acessível para leitura/cópia, como recurso secundário.
- Splash com mínimo padrão de 1,8 s, ajustável nas preferências. O mínimo é contado
  desde sua exibição, não somado ao carregamento; usa timer, nunca sleep. Essa é uma
  mudança explícita em relação ao requisito anterior de não impor duração mínima.

As referências são padrões de ferramentas técnicas e de criação: modos ativos
explícitos, propriedades contextuais, listas ligadas à seleção, painéis recolhíveis
e manipulação direta. Não reproduzimos o layout ou a identidade visual de outro produto.

## Verificação

Preservar a suíte existente e adicionar verificações de seleção direta de rota,
scrub de passos, slider/roda, ícone ativo, criação integrada, matriz pendente,
highlight e temporização não bloqueante. Exercitar fonte e pacote, atualizar as
capturas reais e registrar separadamente qualquer bloqueio no push ou CI.

## Entrega 2.1

A composição foi isolada em `shell.py`, os controles de construção/zoom em
`workspace.py` e os resultados em `result_browser.py`. O navegador usa listas
de rotas e um modelo Qt lazy para etapas; seleção, tabela e slider atualizam o
mesmo índice de reprodução, sem modificar o grafo. Trocar os parâmetros cancela
a consulta anterior e evita apresentar seu resultado sob outro algoritmo.

Gerador e matriz deixaram de ser diálogos. Valores de matriz são preservados ao
mudar tipo/tamanho; conflitos ao remover direção são reportados no painel. Uma
aplicação é uma operação de undo, e parâmetros pendentes não alteram o documento.

O destaque preserva rótulos legíveis, distingue visita e vértice atual e reduz o
contraste de conexões fora do caminho. O relatório continua disponível sem ocupar
altura do canvas automaticamente. O estado nativo da janela foi preservado.

A suíte tem 81 casos aprovados, incluindo clique direto em rota, tabela/scrub de
passos, slider/roda, ferramentas horizontais, física visível em largura de laptop,
construção integrada e mínimo de splash sem bloquear eventos. A cobertura dos
módulos matemáticos/de persistência permanece em 88,65%; Ruff e mypy aprovados.
As capturas em `docs/screenshots/` foram produzidas pela aplicação em Linux
offscreen. A validação visual nativa de Windows/DPI depende do ambiente correspondente.
