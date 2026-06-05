class Vertex:
    def __init__(self, name, available=True):
        """Constructor for the Vertex class.
        Args:
            name (str): Node identifier.
            available (bool): Whether the node is active in the graph.
        """
        self.name = name
        self.neighbors = []
        self.available = available

    def get_name(self) -> str:
        return self.name

    def get_neighbors(self) -> list:
        return self.neighbors

    def get_available(self) -> bool:
        return self.available

    def set_available(self, available: bool):
        self.available = available

    def get_degree(self) -> int:
        return len(self.neighbors)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Vertex({self.name})"