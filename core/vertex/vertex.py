"""
core/vertex/vertex.py — Generic graph vertex
=============================================
Provides the base ``Vertex`` class used by every node in the graph.
``AirportVertex`` (see airport_vertex.py) extends this class with
domain-specific airport data.

Attributes stored per vertex
-----------------------------
name        : Unique string identifier (IATA code for airports).
neighbors   : List of outgoing ``Edge`` objects.  For a directed graph only
              edges that originate at this vertex are stored here.
available   : When ``False`` the vertex is logically removed from traversals
              without being deleted from the graph dictionary.  This mirrors
              the route-blocking mechanic used for network interruptions.
"""


class Vertex:
    """Base node in the flight-network graph.

    Parameters
    ----------
    name : str
        Unique node identifier.  For airports this is the three-letter IATA
        code (e.g. ``"BOG"``, ``"LIM"``).
    available : bool, optional
        Whether the vertex participates in graph traversals.  Defaults to
        ``True``.  Set to ``False`` to simulate a closed airport without
        removing it from the graph structure.
    """

    def __init__(self, name: str, available: bool = True):
        self.name = name
        self.neighbors: list = []   # outgoing Edge objects
        self.available = available

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_name(self) -> str:
        """Return the unique identifier of this vertex."""
        return self.name

    def get_neighbors(self) -> list:
        """Return the list of outgoing edges from this vertex."""
        return self.neighbors

    def get_available(self) -> bool:
        """Return ``True`` if the vertex is active in the graph."""
        return self.available

    def set_available(self, available: bool) -> None:
        """Enable or disable the vertex for graph traversals."""
        self.available = available

    def get_degree(self) -> int:
        """Return the out-degree (number of outgoing edges)."""
        return len(self.neighbors)

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Vertex({self.name})"
