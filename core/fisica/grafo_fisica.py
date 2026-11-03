import math

# Constantes da física
FORCA_ATRACAO = 0.02
FORCA_REPULSAO = 100
AMORTECIMENTO = 0.92
RAIO_REPULSAO = 400
VELOCIDADE_MAX = 10.0
COMPRIMENTO_DESEJADO = 200

def aplicar_fisica(self):
    """
    Aplica forças de repulsão e atração para atualizar posições dos vértices no grafo.
    Deve ser chamado em uma instância que possua `self.grafo` com `vertices` e `arestas`.
    """
    try:
        vertices = list(self.grafo.vertices.values())
        total_vertices = len(vertices)

        # Fase 1: Forças de repulsão entre pares de vértices
        for i in range(total_vertices):
            v1 = vertices[i]
            if v1.fixo or not hasattr(v1, 'vx'):
                continue

            for j in range(i + 1, total_vertices):
                v2 = vertices[j]
                dx = v1.pos().x() - v2.pos().x()
                dy = v1.pos().y() - v2.pos().y()
                dist_sq = dx * dx + dy * dy

                if dist_sq == 0:
                    continue  # Evita divisão por zero

                if dist_sq < RAIO_REPULSAO ** 2:
                    dist = math.sqrt(dist_sq)
                    # Força de repulsão decresce com distância^1.5
                    forca = min(FORCA_REPULSAO / (dist ** 1.5), 50)

                    if not v2.fixo:
                        v1.vx += forca * dx / dist
                        v1.vy += forca * dy / dist
                        v2.vx -= forca * dx / dist
                        v2.vy -= forca * dy / dist

        # Fase 2: Forças de atração ao longo das arestas
        for aresta in self.grafo.arestas:
            n1 = aresta.vertice1
            n2 = aresta.vertice2

            if not all(hasattr(v, 'vx') for v in [n1, n2]):
                continue

            dx = n2.pos().x() - n1.pos().x()
            dy = n2.pos().y() - n1.pos().y()
            dist_sq = dx * dx + dy * dy

            if dist_sq == 0:
                continue

            dist = math.sqrt(dist_sq)
            forca = (dist - COMPRIMENTO_DESEJADO) * FORCA_ATRACAO

            # Limita a força máxima para evitar instabilidade
            forca = max(min(forca, 50), -50)

            if not n1.fixo:
                n1.vx += forca * dx / dist
                n1.vy += forca * dy / dist
            if not n2.fixo:
                n2.vx -= forca * dx / dist
                n2.vy -= forca * dy / dist

        # Fase 3: Atualiza posições dos vértices
        for vertice in vertices:
            if vertice.fixo or not hasattr(vertice, 'vx'):
                continue

            velocidade = math.hypot(vertice.vx, vertice.vy)
            if velocidade > VELOCIDADE_MAX:
                scale = VELOCIDADE_MAX / velocidade
                vertice.vx *= scale
                vertice.vy *= scale

            try:
                new_x = vertice.pos().x() + vertice.vx
                new_y = vertice.pos().y() + vertice.vy
                vertice.setPos(new_x, new_y)
            except Exception as err:
                print(f"Erro ao atualizar posição do vértice {vertice}: {err}")

            # Aplica amortecimento para suavizar movimento
            vertice.vx *= AMORTECIMENTO
            vertice.vy *= AMORTECIMENTO

            # Previne valores NaN
            if math.isnan(vertice.vx):
                vertice.vx = 0.0
            if math.isnan(vertice.vy):
                vertice.vy = 0.0

    except Exception as e:
        print(f"Erro na física: {e}")