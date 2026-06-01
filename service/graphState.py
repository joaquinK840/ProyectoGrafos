"""
Estado global del grafo en memoria.
Módulo compartido para que todos los routers accedan al mismo grafo.
"""

current_graph = None

def get_graph():
    from fastapi import HTTPException
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No hay un grafo cargado")
    return current_graph

def set_graph(graph):
    global current_graph
    current_graph = graph