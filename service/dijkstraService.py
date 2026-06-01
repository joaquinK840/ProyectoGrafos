from core.graph.directed_graph import Directed_Graph
from core.vertex.vertex import Vertex
from core.edge.edge import Edge


def dijkstra_multi(grafo:Directed_Graph, salida:Vertex, filtros:list):
    if not grafo.get_vertex(salida):
        raise ValueError(f"El vértice de salida no existe en el grafo")
    resultados = {}
    #itero y guardo el o los resultados dependiendo de el usuario
    for filtro in filtros:
        resultados[filtro] = dijkstra(grafo, salida, filtro)
    return resultados

def weight_function(filter, edge:Edge) ->float:
    """Función que devuelve la función de peso correspondiente según el filtro seleccionado.
    """
    if filter == 1:
        #si se llamara a Edge en vez de a edge se está llamando la clase mas no la instancia
        return edge.get_distance()
    if filter == 2:
        return edge.get_time()
    if filter == 3:
        return edge.get_cost()
    else:
        raise ValueError(f"la key no es un valor existente")

def dijkstra (grafo,salida, filtro):
    distancia = {}
    nodo_anterior = {}

    for vertex in grafo.vertices.values():
        #no conocemos ninguna ruta por que lo que infinita
        distancia[vertex] = float("inf")
        #el nodo inicial queda en none porque no hay uno antes de el
        nodo_anterior[vertex] = None
    #la distancia del origen hacia si mismo es 0
    distancia[salida] = 0

    #lista con todos los vertices del grafo
    cola_pririodad = list(grafo.vertices.values())
    while cola_pririodad:
        #toma el nodo con menor distancia en la cola de prioridad o por defecto el nodo salida
        nodo_menorDistancia = min (cola_pririodad,key=lambda vertex: distancia[vertex])
        #remueve el nodo "actual" de la cola de prioridad
        cola_pririodad.remove(nodo_menorDistancia)
        for edge in nodo_menorDistancia.get_neighbors():
            #toma los vecinos de el nodo "actual"
            vecino = edge.get_vertex2()
            #validaciones para tomar el camino actual mas corto o modificar uno ya existente
            #si se encuentra uno mejor, garantizando no procesar nodos que ya se han procesado su distancia optima
            if vecino in cola_pririodad:
                peso = weight_function(filtro,edge)
                nueva_Distancia = distancia[nodo_menorDistancia] + peso
                if nueva_Distancia < distancia[vecino]:
                    distancia[vecino] = nueva_Distancia
                    nodo_anterior[vecino] = nodo_menorDistancia
    return distancia, nodo_anterior
    
