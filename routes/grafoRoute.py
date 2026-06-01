import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from schemas.grafoSchema import GraphPayload
from schemas.edgeSchema import EdgePayload
from schemas.vertexSchema import VertexPayload
from core.edge.edge import Edge
from core.vertex.vertex import Vertex
from service.graphService import build_graph, serialize_graph, build_airport_graph, serialize_airport_graph
from service.graphState import get_graph, set_graph

router = APIRouter()


@router.post("/cargar")
def load_graph(payload: GraphPayload):
    try:
        set_graph(build_graph(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"message": "Grafo cargado correctamente", "graph": serialize_graph(get_graph())}


@router.post("/cargar-archivo")
async def load_graph_file(request: Request):
    try:
        data = json.loads((await request.body()).decode("utf-8"))
        set_graph(build_graph(data))
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Archivo JSON invalido") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"message": "Archivo cargado correctamente", "graph": serialize_graph(get_graph())}


@router.post("/cargar-vuelos")
def load_airport_graph(payload: dict):
    try:
        set_graph(build_airport_graph(payload))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_airport_graph(get_graph())


@router.get("/exportar")
def export_graph():
    return JSONResponse(
        content=serialize_graph(get_graph()),
        headers={"Content-Disposition": "attachment; filename=graph.json"},
    )


@router.get("")
def get_graph_endpoint():
    return serialize_graph(get_graph())


@router.get("/aeropuerto/{iata_id}")
def get_airport_detail(iata_id: str):
    graph = get_graph()
    try:
        vertex = graph.get_vertex(iata_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Aeropuerto '{iata_id}' no encontrado")
    return {
        "id": vertex.get_name(),
        "nombre": vertex.get_nombre_completo(),
        "ciudad": vertex.get_ciudad(),
        "pais": vertex.get_pais(),
        "zona_horaria": vertex.get_zona_horaria(),
        "es_hub": vertex.is_hub(),
        "aerolineas": vertex.get_aerolineas(),
        "costo_alojamiento": vertex.get_costo_alojamiento(),
        "costo_alimentacion": vertex.get_costo_alimentacion(),
        "actividades": vertex.get_actividades(),
        "trabajos": vertex.get_trabajos(),
        "grado_salida": vertex.get_degree(),
    }


@router.post("/vertices")
def add_vertex(payload: VertexPayload):
    try:
        get_graph().add_vertex(Vertex(payload.name))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_graph(get_graph())


@router.post("/edges")
def add_edge(payload: EdgePayload):
    graph = get_graph()
    try:
        v1 = graph.get_vertex(payload.vertex1)
        v2 = graph.get_vertex(payload.vertex2)
        graph.add_edge(Edge(v1, v2, payload.weight))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_graph(graph)


@router.get("/vertices/{vertex_name}/vecinos")
def get_neighbors(vertex_name: str):
    graph = get_graph()
    try:
        vertex = graph.get_vertex(vertex_name)
        neighbors = graph.get_neighbors(vertex)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"vertex": vertex_name, "neighbors": [n.get_name() for n in neighbors]}