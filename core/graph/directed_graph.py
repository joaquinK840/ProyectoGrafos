"""
core/graph/directed_graph.py — In-memory directed weighted graph
=================================================================
Provides ``Directed_Graph``, the core data structure used by all planning
algorithms.  The graph stores vertices in a plain ``dict`` keyed by name,
and outgoing edges are stored directly on each ``Vertex.neighbors`` list
(adjacency-list representation).

Structure
---------
vertices : dict[str, Vertex]
    Maps each vertex name (IATA code) to its ``AirportVertex`` instance.
    Lookups are O(1).

Vertex.neighbors : list[AirportEdge]
    Outgoing edges from that vertex.  Only directed edges originating at the
    vertex appear here; no reverse pointer is stored.

Thread safety
-------------
All state is kept in a single in-memory singleton loaded by ``graphState.py``.
The API is single-threaded (single Uvicorn worker), so no locking is needed.
"""

from core.edge.edge import Edge
from core.vertex.vertex import Vertex


class Directed_Graph:
    """Directed weighted graph backed by an adjacency-list representation.

    Vertices are stored in a ``dict`` for O(1) lookup by name.  Each vertex
    owns a ``neighbors`` list of outgoing ``Edge`` (or ``AirportEdge``) objects.
    Algorithms traverse the graph by iterating ``vertex.neighbors`` and calling
    ``edge.get_vertex2()`` to reach the next node.
    """

    def __init__(self):
        self.vertices: dict[str, Vertex] = {}

    def get_edge(self, origen: str, destino: str) -> Edge:
        """Return the directed edge from *origen* to *destino*.

        Parameters
        ----------
        origen : str
            IATA code of the origin airport.
        destino : str
            IATA code of the destination airport.

        Raises
        ------
        ValueError
            If either vertex does not exist or no direct edge connects them.
        """
        vertex = self.get_vertex(origen)
        for edge in vertex.neighbors:
            if edge.get_vertex2().get_name() == destino:
                return edge
        raise ValueError(f"Edge {origen}→{destino} not found in graph")

    def add_vertex(self, vertex: Vertex) -> None:
        """Add a vertex to the graph.

        Parameters
        ----------
        vertex : Vertex
            The vertex to add.  Its ``get_name()`` value must be unique.

        Raises
        ------
        ValueError
            If a vertex with the same name already exists.
        """
        vertex_name = vertex.get_name()
        if vertex_name in self.vertices:
            raise ValueError("Vertex already in graph")
        self.vertices[vertex_name] = vertex

    def add_edge(self, edge: Edge) -> None:
        """Add a directed edge to the graph.

        Appends *edge* to the ``neighbors`` list of its origin vertex so that
        traversals starting at that vertex can discover the edge.  Both
        endpoints must already be registered via ``add_vertex``.

        Parameters
        ----------
        edge : Edge
            The edge to add.  ``edge.get_vertex1()`` is the origin and
            ``edge.get_vertex2()`` is the destination.

        Raises
        ------
        ValueError
            If either endpoint vertex is not present in the graph.
        """
        vertex1 = edge.get_vertex1()
        vertex2 = edge.get_vertex2()
        if vertex1.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex1.get_name()} not in graph")
        if vertex2.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex2.get_name()} not in graph")
        vertex1.neighbors.append(edge)

    def is_vertex_in(self, vertex: Vertex) -> bool:
        """Return ``True`` if *vertex* is registered in the graph."""
        return vertex.get_name() in self.vertices

    def get_vertex(self, vertex_name: str) -> Vertex:
        """Return the vertex with the given name.

        Parameters
        ----------
        vertex_name : str
            IATA code to look up.

        Raises
        ------
        ValueError
            If no vertex with that name exists.
        """
        if vertex_name not in self.vertices:
            raise ValueError(f"Vertex {vertex_name} not in graph")
        return self.vertices[vertex_name]

    def get_neighbors(self, vertex: Vertex) -> list[Vertex]:
        """Return a list of destination vertices reachable from *vertex*.

        Parameters
        ----------
        vertex : Vertex
            The origin vertex whose outgoing neighbours are requested.

        Raises
        ------
        ValueError
            If *vertex* is not registered in the graph.
        """
        if vertex.get_name() not in self.vertices:
            raise ValueError(f"Vertex {vertex.get_name()} not in graph")
        return [edge.get_vertex2() for edge in vertex.neighbors]

    def __str__(self) -> str:
        result = ""
        for vertex in self.vertices.values():
            result += f"{vertex.get_name()}: {', '.join(str(edge) for edge in vertex.neighbors)}\n"
        return result
