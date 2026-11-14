# Linguagem visual

Grafla é um editor técnico: canvas prioritário, controles compactos e propriedades
contextuais. A identidade usa a nova marca enviada pelo autor, com tipografia
forte, superfícies neutras e laranja reservado para ação/seleção.

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

## Marca do aplicativo

Os quatro arquivos recebidos em `grafla.zip` estão em `src/grafla/resources/`,
sem alterações no desenho, nas cores ou na transparência:

| Arquivo recebido | Recurso no pacote | Uso |
| --- | --- | --- |
| `grafla.png` | `grafla.png` | Janela, diálogos e símbolo no canto superior direito |
| `grafla_icone.ico` | `grafla.ico` | Ícone do executável Windows |
| `Grafla ícone alt.png` | `grafla-horizontal.png` | Marca horizontal na abertura |
| `Grafla ícone alt 2.png` | `grafla-vertical.png` | Marca vertical na tela Sobre |

`branding.py` concentra a leitura das imagens, preserva a proporção e mantém um
cache por tamanho e escala. O ícone da janela deriva de uma única leitura a 256 px;
os tamanhos menores são preparados em memória, sem decodificar o PNG a cada uso.
O empacotamento inclui as quatro imagens.

O cabeçalho do documento ocupa toda a largura da janela, acima do canvas e dos
painéis. O símbolo à direita abre Sobre e pode receber foco pelo teclado.
As marcas com texto branco usam uma superfície escura também no tema claro.
A splash tem cantos arredondados, fundo discreto, versão e progresso real; mantém
o mínimo configurável e encerra os timers e a animação ao fechar.

## Canvas e controles

Seleção tem contorno tracejado; execução tem ring no vértice atual, traço mais
espesso, lista de visitados e fila/pilha. Feedback não depende exclusivamente de
cor. O grid de pontos adapta a densidade ao zoom e pode ser desligado.

O inspector usa Apply explícito, sem misturar alteração instantânea com um botão
Salvar fictício. Cores são editadas como #RRGGBB, validadas na transação. Inputs,
checkboxes e combos recebem o estilo do tema e labels de formulário.

Os painéis laterais são recolhíveis e a análise tem scroll para telas menores.
O relatório é um dock secundário que o usuário abre quando precisa copiar detalhes.
O zoom usa layout Qt, sem posicionamento absoluto sobre o canvas. A janela usa
drag/resize e controles nativos do SO.

Na revisão 2.1, ferramentas e ações contextuais ficam numa faixa horizontal.
O zoom tem sua própria faixa abaixo do canvas, com slider logarítmico, ±, 100%,
ajuste, grade e snap. Rotas são escolhas diretas, com destaque no canvas; passos
têm uma tabela de visitas e slider temporal. O relatório não abre automaticamente.
O contexto sem destaque mantém rótulos legíveis; visitas são verde-azuladas,
o vértice atual tem ring laranja e a seleção continua com contorno explícito.

O estado vazio apresenta criação e atalhos discretos. Mensagens normais usam a
status bar; validação também aparece no painel de status, e logs guardam detalhes.
Modais são reservados a configuração/arquivo e confirmação de trabalho não salvo.

Qt 6 trata escala DPI. Ícones vetoriais e layouts ajudam, mas não equivalem a
certificar 125/150/200% em todos os monitores. Acessibilidade do canvas pintado
também não é automaticamente equivalente à de uma lista nativa de objetos;
a busca por ID/rótulo fornece navegação adicional por teclado nesta versão.

## Ferramentas e movimento

As novas silhuetas seguem a família original do autor: mão com dedos arredondados,
borracha diagonal, vértice circular com adição e conexão diagonal. Inativo usa
contorno de 1,65 unidades numa grade de 24; ativo troca a geometria por uma massa
preenchida, sem depender de pequenos pontos internos. QIcon fornece Normal,
Active, Selected e Disabled, com variantes Off/On e múltiplas resoluções em cache.
O laranja compartilhado continua sendo a cor de ação; o desabilitado mistura
texto secundário e canvas para reduzir contraste nos dois temas.

A transição de 110 ms usa apenas a opacidade do botão, pode ser interrompida e
pode ser desligada nas preferências. Timer e efeito ficam inativos em repouso.
A faixa contextual tem altura constante e apresenta o gesto disponível; cancelar
uma conexão não muda a altura do canvas. Origem de aresta tem ring sólido e
preenchimento suave; seleção conserva o tracejado.

A aba Física apresenta estado, ativação e pausa separados. Quatro controles
principais e três perfis atendem aos ajustes comuns. O disclosure de ajustes
avançados revela controles adicionais sem sugerir que eles estavam desativados.
Sliders e campos numéricos ficam sincronizados; setas compartilhadas e área de
texto verificada evitam controles vazios após troca de tema. A barra compacta
mantém modos, ativação, pausa e ajustes acessíveis também a 1024 px com fonte maior.
