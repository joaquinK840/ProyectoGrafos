from core.edge.edge import Edge
from core.graph.directed_graph import Directed_Graph

class Undirected_graph(Directed_Graph):
    def add_edge(self, edge):
        Directed_Graph.add_edge(self, edge)
        # Agregar la arista en sentido contrario para que sea no dirigido
        edge_back = Edge(edge.get_vertex2(),edge.get_vertex1(),edge.get_weight())
        Directed_Graph.add_edge(self, edge_back)
