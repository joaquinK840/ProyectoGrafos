"""
service/graphState.py — In-memory graph singleton
==================================================
Holds the single ``Directed_Graph`` instance shared by all route handlers.

The API is stateful by design: the client uploads a JSON network file once
(via POST /grafo/cargar), which builds the graph and stores it here.
All subsequent requests (pathfinding, planning, interruptions) read from
this singleton without re-parsing the JSON.

Thread safety
-------------
The API runs as a single-worker Uvicorn process, so no locking is required.
If the API is ever scaled to multiple workers, this module would need to be
replaced with a shared store (Redis, database, etc.).
"""

current_graph = None


def get_graph():
    """Return the currently loaded graph instance.

    Raises
    ------
    HTTPException (404)
        If no graph has been loaded yet (``POST /grafo/cargar`` not called).
    """
    from fastapi import HTTPException
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No hay un grafo cargado")
    return current_graph


def set_graph(graph):
    """Replace the in-memory graph with a newly built instance.

    Called by the graph-upload endpoint after ``graphRepository.load_graph``
    and the builder have constructed the full ``Directed_Graph``.

    Parameters
    ----------
    graph : Directed_Graph
        The fully initialised graph to store.
    """
    global current_graph
    current_graph = graph