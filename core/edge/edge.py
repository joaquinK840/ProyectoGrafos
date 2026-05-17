from core.vertex.vertex import Vertex
class Edge:
    def __init__(self, vertex1: Vertex, vertex2: Vertex,distance = 0, time = 0, cost = 0):
        """Constructor for the Edge class.
        Args:
            vertex1 (Vertex): Nodo origen instancia de la clase Vertex.
            vertex2 (Vertex): Nodo destino instancia de la clase Vertex.
            weight (int): Peso de la arista.
        """
        if vertex1 is None:
            raise ValueError("Origin vertex not found in graph")
        if vertex2 is None:
            raise ValueError("Destination vertex not found in graph")
        if distance < 0:
            raise ValueError("Distance must be non-negative")
        if time < 0:
            raise ValueError("Time must be non-negative")
        if cost < 0:
            raise ValueError("Cost must be non-negative")
        self.vertex1 = vertex1
        self.vertex2 = vertex2
        self.distance = distance
        self.time = time
        self.cost = cost

        #getters y setters
    def get_vertex1(self):
        """Devuelve el nodo origen de la arista.
        Returns:
            str: Nodo origen.
        """
        return self.vertex1
    def get_vertex2(self):
        """Devuelve el nodo destino de la arista.
        Returns:
            str: Nodo destino.
        """
        return self.vertex2
    
    def get_time(self):
        """Devuelve el tiempo de la arista.
        Returns:
            int: Tiempo de la arista.
        """
        return self.time
    
    def get_distance(self):
        """Devuelve la distancia de la arista.
        Returns:
            int: Distancia de la arista.
        """
        return self.distance
    
    def get_cost(self):
        """Devuelve el costo de la arista.
        Returns:
            int: Costo de la arista.
        """
        return self.cost
    
    def __str__(self):
        """Devuelve una cadena que representa la arista.
        Returns:
            str: Cadena que representa la arista.
        """
        return f"{self.vertex1.get_name()} --{self.distance}--> {self.vertex2.get_name()}"
        
        
