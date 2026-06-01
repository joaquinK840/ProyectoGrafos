import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core.edge.edge import Edge
from core.vertex.vertex import Vertex
from schemas.dfsSchema import DFSFilterResponse, DFSMultiResponse, DFSPayload
from schemas.dijkstraSchema import (DijkstraFilterResponse,
                                    DijkstraMultiResponse,
                                    DijkstraNodeResponse, DijkstraPayload)
from schemas.edgeSchema import EdgePayload
from schemas.grafoSchema import GraphPayload
from schemas.vertexSchema import VertexPayload
from service.dfsService import dfs_multi
from service.dijkstraService import dijkstra_multi
from service.graphService import build_graph, serialize_graph

router = APIRouter()

current_graph = None



def get_current_graph():
    if current_graph is None:
        raise HTTPException(status_code=404, detail="No hay un grafo cargado")
    return current_graph


@router.post("/cargar")
def load_graph(payload: GraphPayload):
    """Carga un grafo desde JSON enviado por el frontend."""
    global current_graph
    try:
        current_graph = build_graph(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "message": "Grafo cargado correctamente",
        "graph": serialize_graph(current_graph),
    }


@router.post("/cargar-archivo")
async def load_graph_file(request: Request):
    """Carga el contenido de un archivo JSON enviado como cuerpo de la peticion."""
    global current_graph
    try:
        data = json.loads((await request.body()).decode("utf-8"))
        current_graph = build_graph(data)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Archivo JSON invalido") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "message": "Archivo cargado correctamente",
        "graph": serialize_graph(current_graph),
    }


@router.get("/exportar")
def export_graph():
    graph = get_current_graph()
    return JSONResponse(
        content=serialize_graph(graph),
        headers={"Content-Disposition": "attachment; filename=graph.json"},
    )


@router.get("")
def get_graph():
    return serialize_graph(get_current_graph())


@router.post("/vertices")
def add_vertex(payload: VertexPayload):
    graph = get_current_graph()
    try:
        graph.add_vertex(Vertex(payload.name))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_graph(graph)


@router.post("/edges")
def add_edge(payload: EdgePayload):
    graph = get_current_graph()
    try:
        vertex1 = graph.get_vertex(payload.vertex1)
        vertex2 = graph.get_vertex(payload.vertex2)
        graph.add_edge(Edge(vertex1, vertex2, payload.weight))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_graph(graph)


@router.get("/vertices/{vertex_name}/vecinos")
def get_neighbors(vertex_name: str):
    graph = get_current_graph()
    try:
        vertex = graph.get_vertex(vertex_name)
        neighbors = graph.get_neighbors(vertex)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "vertex": vertex_name,
        "neighbors": [neighbor.get_name() for neighbor in neighbors],
    }

@router.post("/shortRoute")
def get_shortRoute(payload: DijkstraPayload):
    """Calcula las rutas más cortas usando el algoritmo de Dijkstra con múltiples filtros."""
    graph = get_current_graph()
    try:
        start_vertex = graph.get_vertex(payload.start_vertex)
        results = dijkstra_multi(graph, start_vertex, payload.filters)
        
        filter_names = {1: "distance", 2: "time", 3: "cost"}
        responses = []
        
        for filter_id in payload.filters:
            distancia, nodo_anterior = results[filter_id]
            filter_results = []
            
            for vertex, dist in distancia.items():
                previous = nodo_anterior[vertex].get_name() if nodo_anterior[vertex] else None
                filter_results.append(DijkstraNodeResponse(
                    vertex=vertex.get_name(),
                    distance=dist,
                    previous=previous
                ))
            
            responses.append(DijkstraFilterResponse(
                filter_id=filter_id,
                filter_name=filter_names.get(filter_id, "unknown"),
                results=filter_results
            ))
        
        return DijkstraMultiResponse(
            start_vertex=payload.start_vertex,
            responses=responses
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/dfs")
def get_dfs(payload: DFSPayload):
    """Recorre el grafo usando DFS con un peso máximo limitado y múltiples filtros."""
    graph = get_current_graph()
    try:
        start_vertex = graph.get_vertex(payload.start_vertex)
        results = dfs_multi(graph, start_vertex, payload.max_weight, payload.filters)
        
        filter_names = {1: "distance", 2: "time", 3: "cost"}
        responses = []
        
        for filter_id in payload.filters:
            visited = results[filter_id]
            responses.append(DFSFilterResponse(
                filter_id=filter_id,
                filter_name=filter_names.get(filter_id, "unknown"),
                visited_vertices=visited,
                total_count=len(visited)
            ))
        
        return DFSMultiResponse(
            start_vertex=payload.start_vertex,
            max_weight=payload.max_weight,
            responses=responses
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error