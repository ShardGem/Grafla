from core.modelos.grafo_vertice import GrafoVertice
from core.modelos.grafo_aresta import GrafoAresta

'''
CLASSE DO GRAFO

- Cria o conjunto de vertices e arestas que compoem o grafo e manipula eles.
'''
class Grafo:
    def __init__(self):
        super().__init__()

        self.vertices = {} # Dicionário que vai armazenar os ids e objeto do vértice. Ex: {vertice_id : GrafoVertice}.
        self.arestas = [] # Lista de arestas.

    ''' -------------------------------------
                MANIPULAR GRAFO
    ------------------------------------- '''
    def adicionar_vertice(self, proximo_vertice_id, cor_padrao, x=960, y=540):
        vertice = GrafoVertice(proximo_vertice_id, x, y, cor=cor_padrao)

        print(f'Vértice {proximo_vertice_id} criado em ({x}, {y})')  # Debug

        self.vertices[vertice.vertice_id] = vertice
        return vertice

    def adicionar_aresta(self, vertice1, vertice2, cor, ponderado=False, direcionado=True, peso=1):
        """
          Cria um GrafoAresta ligando vertice1 e vertice2, com atributos:
          - cor: QColor ou equivalente (para desenhar)
          - ponderado: bool (se False, ignoramos 'peso' e forçamos peso = 1.0)
          - direcionado: bool
          - peso: float ou int (peso da aresta, se ponderado=True)
          Adiciona em self.arestas e retorna o objeto; se algum vértice for None,
          retorna None.
          """
        if vertice1 is None or vertice2 is None:
            return None

        aresta = GrafoAresta(
            vertice1=vertice1,
            vertice2=vertice2,
            cor=cor,
            ponderado=ponderado,
            direcionado=direcionado,
            peso=peso,
        )

        print(f'Aresta criada entre {vertice1.vertice_id} e {vertice2.vertice_id}')
        self.arestas.append(aresta)
        return aresta

    def remover_vertice(self, vertice):
        """
        Remove o vértice do dicionário self.vertices e também todas as arestas
        que envolvem esse vértice deverão ser removidas
        """
        # Obtém a chave (ID) correspondente ao objeto 'vertice'
        try:
            index_vertice = list(self.vertices.keys())[list(self.vertices.values()).index(vertice)]
        except ValueError:
            return
        self.vertices.pop(index_vertice)
        self.remover_arestas(vertice)

    def remover_arestas(self, vertice):
        vertice_id = vertice.vertice_id
        self.arestas = [
            aresta for aresta in self.arestas
            if vertice_id not in aresta.get_vertices()
        ]

    def esta_diretamente_conectado(self, vertice_a: GrafoVertice, vertice_b: GrafoVertice) -> bool:
        for aresta in self.arestas:
            v1 = aresta.vertice1
            v2 = aresta.vertice2
            if (v1 == vertice_a and v2 == vertice_b) or (v1 == vertice_b and v2 == vertice_a):
                return True
        return False

    def criar_dicionario_adjacencia(self) -> dict[int, list[tuple[int, int]]]:
        """
        Retorna: { vertice_id: [(viz_id, peso), …], … }
        - Se aresta.direcionado == False: adiciona (v1→v2) e (v2→v1)
        - Se aresta.direcionado == True: só (v1→v2)
        - Se aresta.ponderado == False: faz peso_int = 1
        - Se aresta.ponderado == True: peso_int = aresta.peso (já inteiro)
        """
        adjacencia: dict[int, list[tuple[int, int]]] = {
            v_id: [] for v_id in self.vertices
        }

        for aresta in self.arestas:
            v1_id = aresta.vertice1.vertice_id
            v2_id = aresta.vertice2.vertice_id

            if getattr(aresta, "ponderado", False):
                peso_int = int(aresta.peso)
            else:
                peso_int = 1

            if getattr(aresta, "direcionado", False):
                adjacencia[v1_id].append((v2_id, peso_int))
            else:
                adjacencia[v1_id].append((v2_id, peso_int))
                adjacencia[v2_id].append((v1_id, peso_int))

        return adjacencia

    def eh_direcionado(self):
        return any(aresta.direcionado for aresta in self.arestas)