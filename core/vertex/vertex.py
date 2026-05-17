class Vertex:
    def __init__(self, name, available=True):
        """Constructor for the vertex class.
        Args:
            name (str): Nombre del nodo.
            available (bool): Indica si el nodo está disponible.
        """
        self.name = name
        self.neighbors = []
        self.available = available
        
    def get_name(self):
        """Devuelve el nombre del nodo.
        Returns:
            str: Nombre del nodo.
        """
        return self.name
    def get_neighbors(self):
        """Devuelve una lista de los nodos vecinos del nodo.
        Returns:
            list: Lista de los nodos vecinos del nodo.
        """
        return self.neighbors
    def get_available(self):
        """Devuelve el estado de disponibilidad del nodo.
        Returns:
            bool: True si el nodo está disponible, False en caso contrario.
        """
        return self.available
    def set_available(self, available):
        """Establece el estado de disponibilidad del nodo.
        Args:
            available (bool): Nuevo estado de disponibilidad del nodo.
        """
        self.available = available
    def __str__(self): #imprimir el diccionario del nodo
        """Devuelve una cadena que representa el nodo.
        Returns:
            str: Cadena que representa el nodo.
        """
        return self.name
