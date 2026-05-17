import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from schemas.grafoSchema import GraphPayload
from schemas.edgeSchema import EdgePayload
from schemas.vertexSchema import VertexPayload

from core.edge.edge import Edge
from core.vertex.vertex import Vertex
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
