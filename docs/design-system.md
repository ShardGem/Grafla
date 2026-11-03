# Linguagem visual

Grafla é um editor técnico: canvas prioritário, controles compactos e propriedades
contextuais. A identidade mantém o nome e o ícone original do aplicativo, com
tipografia forte, superfícies neutras e laranja reservado para ação/seleção.

Tokens são definidos em `src/grafla/theme.py`. QPalette/QSS estilizam widgets;
os itens gráficos usam o mesmo objeto Theme. Há Dark, Light e System. A troca de
tema não muda dados, histórico ou resultados.

| Papel | Dark | Light |
|---|---|---|
| Fundo | `#171c24` | `#edf1f7` |
| Superfície | `#202733` | `#ffffff` |
| Painel | `#252e3b` | `#f4f6fa` |
| Canvas | `#11161e` | `#fafbfd` |
| Borda | `#394455` | `#bac6d5` |
| Texto | `#edf2f8` | `#202b3b` |
| Secundário | `#aebacc` | `#4d6078` |
| Accent/foco | `#ffad78` | `#a84617` |
| Hover/selected surface | `#303d4e` | `#e0e7f1` |
| Erro/perigo | `#ff929f` | `#b52842` |

Fonte de sistema via QFontDatabase, base de 10 pt; brand e cabeçalhos estabelecem
hierarquia. Espaçamentos 4/8/12/16/24, bordas de um pixel lógico e raios discretos.
Ícones da toolbar são vetores SVG centrais renderizados/cacheados em múltiplas
resoluções; não existem PNGs diferentes para cada estado de hover/click.

Seleção tem contorno tracejado; execução tem ring no vértice atual, traço mais
espesso, lista de visitados e fila/pilha. Feedback não depende exclusivamente de
cor. O grid de pontos adapta a densidade ao zoom e pode ser desligado.

O inspector usa Apply explícito, sem misturar alteração instantânea com um botão
Salvar fictício. Cores são editadas como #RRGGBB, validadas na transação. Inputs,
checkboxes e combos recebem o estilo do tema e labels de formulário.

Os painéis laterais são recolhíveis e a análise tem scroll para telas menores.
O dock de resultados abre quando necessário. Zoom fica na status bar, com layout
Qt, sem posicionamento absoluto sobre o canvas. A janela usa drag/resize e
controles nativos do SO.

O estado vazio apresenta criação e atalhos discretos. Mensagens normais usam a
status bar; validação também aparece no painel de status, e logs guardam detalhes.
Modais são reservados a configuração/arquivo e confirmação de trabalho não salvo.

Qt 6 trata escala DPI. Ícones vetoriais e layouts ajudam, mas não equivalem a
certificar 125/150/200% em todos os monitores. Acessibilidade do canvas pintado
também não é automaticamente equivalente à de uma lista nativa de objetos;
a busca por ID/rótulo fornece navegação adicional por teclado nesta versão.
