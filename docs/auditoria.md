# Auditoria e decisões da reformulação

## Base recebida e planejamento

O repositório remoto tinha somente README. O pacote enviado continha 82 arquivos:
23 Python, dois specs, quatro documentos Markdown, requirements e 52 assets.
O legado foi preservado no commit `a9c310d` antes de qualquer modernização.

Antes da implementação, foram lidos os módulos, imports, specs e documentação;
o aplicativo foi iniciado com as versões exatas e exercitado por sondagens em
Linux offscreen. A auditoria inicial completa foi entregue separadamente na conversa.
As mudanças seguem o plano: integridade → domínio/documento → comandos/arquivos →
canvas → interface/física → análises → testes/build/documentação.

## Problemas confirmados e solução

| Legado | Consequência | Correção e verificação |
|---|---|---|
| Aresta removida da cena antes de procurar sua view | Ligação invisível continuava no modelo | Remoção pelo documento, projeção por IDs; teste de clique/Delete/undo |
| Cancelamento de limpeza sem retorno | Importação continuava; gerador voltava a perguntar | Gerador/matriz preparam dados e só substituem após aceite; operação desfazível |
| Ambas as metades da matriz simétrica geravam arestas | Uma ligação virava duas | Conversão percorre uma metade; teste 2×2 e peso zero |
| Limite de tentativas diminuía com arestas restantes | Pedido de seis ligações produzia cinco | Amostra de pares únicos com capacidade validada; testes de grafos completos |
| Peso 1 ignorado na soma | Rota 1+2 informava custo 2 | Custo efetivo centralizado, NetworkX e teste de custo 3 |
| Rotas sobreviviam a exclusões | Navegação gerava KeyError | Snapshot/revisão, cancelamento e invalidação por edição |
| Sinal de rótulo inexistente / edição sem aviso | Painéis desatualizados e AttributeError | Eventos do documento; inspector e seletores integrados |
| Método de direção testado sem chamada | Regra de duplicata sempre escolhia o ramo dirigido | Política explícita de pares, validada no domínio |
| Seta pintada fora dos bounds | Cortes e invalidação incorreta | Bounds/shape incluem desenho e hit; regressão de geometria |
| Timer global de 10 ms, mais um por vértice | Processamento contínuo, mesmo parado | Canvas orientado a eventos; animações/física possuem ciclos de vida próprios |
| Busca da aresta oposta percorria toda a cena | Custo de varreduras E×(V+E) por atualização | Mapas de pares e incidentes; teste de atualização só das incidentes |
| Layout conectava sinais em cada resize | Callbacks acumulados | Conexões feitas uma vez na composição da janela |
| Paths de ícones diferiam em caixa | Ferramentas invisíveis em Linux | Vetores centrais e assets do pacote com nomes consistentes |
| Abrir/Salvar/Exportar eram prints | Interface prometia operações inexistentes | Arquivos reais, save atômico, exportações exercitadas e cancelamento testado |

## Decisões tecnológicas

**Manter PyQt6/Widgets/Graphics View.** PyQt6 6.12.0 já estava atualizado. O gargalo
era a varredura implementada pela aplicação, não uma limitação demonstrada do
binding. Migrar para QML ou outro binding junto da extração do domínio aumentaria
o risco de regressão. A identidade unificada foi implementada com a tecnologia atual.
PySide6 continua uma alternativa caso distribuição/licença justifiquem uma migração
isolada. Não foi instalado um segundo binding no produto.

**Domínio próprio + NetworkX.** A aplicação mantém IDs, estilo, posição, documento
e regras. NetworkX 3.7 é adaptado para análises. igraph/rustworkx só justificam
novo backend quando medições de análise o exigirem; não resolvem o antigo loop
de renderização. O visualizador tem dados de passos independentes de widgets.

**Comandos e patches.** Vários caminhos antigos de mutação geravam divergências.
Uma transação validada e patches com inversas tornam exclusões, movimento, geração,
layout e física desfazíveis sem guardar o grafo inteiro em cada entrada do histórico.

**Janela nativa.** A implementação manual removia moldura e controles e tentava
reconstruir movimento, maximização e cantos. Não havia justificativa documentada
que compensasse perder resize/Snap/comportamentos de plataforma. A janela agora
usa QMainWindow normal, mantendo o guard de alterações não salvas no closeEvent.

**Física explícita.** A física antiga estava comentada e não era a causa da CPU
em repouso. Foi isolada em passo matemático e controlador com on/off, limites,
vértices fixados, separação de coincidentes e estabilização. Desligar não restaura
coordenadas antigas; reativar começa nas posições atuais, com velocidades zeradas.

**Ícones vetoriais.** Os PNGs antigos somavam menos de 1 MB comprimido: sua remoção
não é apresentada como grande otimização de memória. A troca simplifica estados,
portabilidade e DPI. O ícone original do aplicativo foi preservado.

**Build único onedir.** Os dois specs divergiam de entrypoint e assets. Um spec
com recursos/metadata, sem UPX e com versão central facilita diagnóstico. A CI
prepara Windows no Windows; um pacote Linux não é um executável Windows validado.

## Performance

Legado, cadeia esparsa E=V−1, uma chamada global sem movimento:

| Vértices | Atualização global |
|---:|---:|
| 100 | 6,05 ms |
| 500 | 119,81 ms |
| 1.000 | 519,06 ms |
| 5.000 | 15.247,62 ms |

Até 1.000 são medianas de três amostras; 5.000 é amostra única. Perfil de 1.000:
aproximadamente 99% em reposicionar arestas; 999 consultas a `scene.items()` e
4,99 milhões de chamadas a isinstance por ciclo. Física estava desligada.

Nova versão, mesma cadeia e viewport 960×680, medianas de três amostras:

| Vértices | Movimento visual de um nó | Commit com undo | Render do viewport |
|---:|---:|---:|---:|
| 100 | 0,15 ms | 1,72 ms | 2,85 ms |
| 500 | 0,12 ms | 7,43 ms | 5,90 ms |
| 1.000 | 0,12 ms | 16,47 ms | 5,90 ms |
| 5.000 | 0,17 ms | 87,54 ms | 6,38 ms |

Zero alterações de cena foram observadas em 100 ms de repouso nos quatro tamanhos.
Os dados completos estão em [benchmark-linux.jsonl](benchmark-linux.jsonl). Foram
medidos sem testes/build simultâneos, com Python 3.12.14 e Qt 6.12.0 no Linux
offscreen. A atualização antiga de todos os elementos e o movimento novo de um
nó **são cargas diferentes**: não se deve calcular “vezes mais rápido” diretamente
entre elas. A mudança principal é eliminar o trabalho sem evento e limitar a
invalidação ao que realmente mudou. Esses números não são FPS nem garantia para
grafos densos ou Windows.

## Validação e limites da entrega

Ruff verifica todo o código ativo; mypy verifica domínio, persistência, algoritmos
e física. pytest combina unitários, integração, UI real via QtTest e subprocesso
do bootstrap. O build onedir Linux foi iniciado em offscreen e encerrado com sucesso.

Não há resultado local de Windows/macOS, assinatura de executável, leitores de tela
ou matriz de monitores físicos/DPI. A CI contém jobs Linux/Windows, Python 3.12/3.14,
build Windows e smoke nativo; seu resultado deve ser observado após o push. A nova
versão não anuncia formatos/algoritmos ainda não implementados.
