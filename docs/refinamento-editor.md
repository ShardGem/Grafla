# Refinamento de interações, histórico e física

## Diagnóstico e responsabilidades

A revisão começou pela arquitetura existente e por uma execução de referência dos
81 testes. Canvas e GraphicsItems cuidam dos gestos/seleção; Document/GraphCommand
são a fronteira de mutação; PhysicsController agenda o passo puro de physics.py.
Ícones e temas são centralizados. Os assets legados preservados foram consultados
antes de redesenhar a mão, a borracha, o vértice e a conexão.

O duplo clique abria propriedades em qualquer ferramenta, embora o press de
arestas fosse consumido separadamente. Move/release também podiam chegar ao Qt
fora do modo de seleção. No histórico, Undo/Redo emitia before_edit, que consolidava
o preview físico. A mudança histórica resultante acordava a simulação novamente,
permitindo movimento e novos comandos imediatamente após restaurar o estado.
Comandos de atributos ainda substituíam o vértice inteiro, incluindo posições
que não pertenciam à edição.

## Contratos resultantes

- Seleção Qt permanece única. Somente Selecionar encaminha gestos de seleção e
  movimento; Mão preserva os elementos selecionados. Construção não os seleciona.
- Dois cliques no mesmo vértice criam um laço quando permitido, sem abrir o
  inspector. Desabilitar laços transforma a repetição em cancelamento.
- Fundo/Esc, troca de modo, reset e histórico encerram uma conexão pendente.
  Conexão em sequência só adota o destino como nova origem após sucesso.
- Snap afeta apenas vértices realmente movidos; clique e movimento de outro
  vértice não arredondam coordenadas de elementos não tocados.
- Comandos de atributos possuem apenas os campos alterados. A sessão de física
  possui apenas coordenadas. O preview é registrado uma vez, sem reaplicá-lo.
- Undo/Redo para o timer, limpa velocidades e preserva a pausa até Retomar.
  Dessa forma, a simulação não invalida a ramificação de redo com novos comandos.
- Rótulos/estilos e ajustes de parâmetros não reiniciam uma sessão em movimento.
  Posições/fixação/topologia, salvar e fechar consolidam o preview antes da ação.
- PhysicsParameters é imutável e valida limites. Valores persistidos inválidos
  usam o padrão correspondente sem descartar outras preferências válidas.
- Pausa, ativação e repouso são distintos. Não há timer contínuo em repouso.

A apresentação não replica o estado do controller: o painel recebe a autoridade
atual e emite pedidos de ação/configuração. Preferências ficam fora do .grafla.
Os ajustes avançados são apenas recolhidos; seus valores continuam válidos.

## Verificação

Os testes incluem cliques/duplo clique reais do Qt, seleção individual/múltipla e
retangular, cancelamento, laços, sequência, snap, modos e navegação temporária.
Histórico é exercitado com simulação em movimento, repetição de Undo/Redo, retomada,
edição de atributos e ajuste de parâmetros sem reiniciar o timer. A matemática
verifica força/direção, alcance, rigidez, amortecimento, velocidade, limites,
coincidentes, fixados e valores finitos em configurações agressivas.

As capturas são janelas reais do Qt em Linux offscreen, nos dois temas. A área de
texto dos números e a disponibilidade das ferramentas são verificadas com fonte
maior e janelas de laptop. A validação nativa de Windows/DPI depende de uma sessão na plataforma;
não foi presumida a partir do teste offscreen.

## Medição reproduzível

```bash
QT_QPA_PLATFORM=offscreen uv run python tools/benchmark.py 100 500 1000
QT_QPA_PLATFORM=offscreen uv run python tools/benchmark.py --physics 100 500 1000
```

O segundo modo mede 12 passos do controller e da sincronização com o canvas,
renderização em imagem separada e consolidação final no histórico. A cadeia é
esparsa (E = V − 1), com posições numa grade e viewport de 960×680 ajustado ao
grafo. Testes e build devem estar parados durante a medição. Estes tempos não
são FPS nem promessa de desempenho para outras densidades, máquinas ou sistemas.

## Resultado local desta revisão

123 testes aprovados, Ruff e mypy aprovados. A cobertura dos módulos de domínio,
persistência, algoritmos e física foi 89,35%; o motor de física atingiu 95%.
O pacote onedir Linux foi construído e seu entrypoint executou o smoke test com
roundtrip .grafla, BFS, física e exportações PNG/JPEG/SVG/PDF.

Comparação com a base `b2d88a9`, em execuções sequenciais com Python 3.12.14 e
Qt 6.12.0 no mesmo ambiente Linux offscreen:

| Vértices | Passo + canvas antes / depois | Render antes / depois | Consolidar histórico antes / depois |
|---:|---:|---:|---:|
| 100 | 4,27 / 3,45 ms | 9,62 / 7,87 ms | 5,22 / 0,81 ms |
| 500 | 25,04 / 19,34 ms | 39,96 / 32,85 ms | 26,20 / 3,98 ms |
| 1.000 | 44,83 / 41,87 ms | 87,76 / 65,87 ms | 46,38 / 7,58 ms |

Os dados estão em [antes](benchmark-physics-before.jsonl),
[depois](benchmark-physics-linux.jsonl) e [canvas](benchmark-editor-linux.jsonl).
O benchmark do canvas observou zero notificações de mudança em 100 ms de repouso
nos quatro tamanhos (100, 500, 1.000 e 5.000 vértices). O movimento visual de um
vértice ficou entre 0,10 e 0,23 ms nessa execução; commits ainda comparam/clonam o
grafo e custaram 97,72 ms a 5.000 vértices. A física a 1.000 vértices ainda supera
o intervalo do timer nesta carga; os resultados não garantem 30 FPS. Densidade,
velocidade configurada, labels e plataforma alteram os custos.
