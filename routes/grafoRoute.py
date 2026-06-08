import json
import math


from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from schemas.grafoSchema import GraphPayload, AirportGraphPayload
from schemas.edgeSchema import EdgePayload
from schemas.vertexSchema import VertexPayload
from core.edge.edge import Edge, normalize_aircraft_config, normalize_aircraft_name
from core.vertex.vertex import Vertex
from service.graphService import build_graph, serialize_graph, build_airport_graph, serialize_airport_graph
from service.graphState import get_graph, set_graph

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────

def _is_airport_graph(graph) -> bool:
    return any(hasattr(v, "es_hub") for v in graph.vertices.values())

def _serialize_current_graph() -> dict:
    graph = get_graph()
    return serialize_airport_graph(graph) if _is_airport_graph(graph) else serialize_graph(graph)

def sanitize_floats(obj):
    """Recursively replaces inf/nan float values with None for JSON compliance."""
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_floats(i) for i in obj]
    return obj


# ── Carga ──────────────────────────────────────────────────────────────

@router.post("/cargar")
def load_graph(payload: GraphPayload):
    """Loads a generic graph from a simple vertex/edge payload."""
    try:
        set_graph(build_graph(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"message": "Grafo cargado correctamente", "graph": serialize_graph(get_graph())}


@router.post("/cargar-archivo")
async def load_graph_file(request: Request):
    """Loads a graph from raw JSON body — auto-detects airport vs generic format."""
    try:
        data = json.loads((await request.body()).decode("utf-8"))
        graph = build_airport_graph(data) if "nodos" in data and "aristas" in data else build_graph(data)
        set_graph(graph)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Archivo JSON inválido") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"message": "Archivo cargado correctamente", "graph": _serialize_current_graph()}


@router.post("/cargar-vuelos")
def cargar_vuelos(payload: AirportGraphPayload):
    try:
        graph = build_airport_graph(payload.model_dump())
        set_graph(graph)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_airport_graph(get_graph())


@router.get("")
def get_graph_endpoint():
    return _serialize_current_graph()


@router.get("/exportar")
def export_graph():
    return JSONResponse(
        content=_serialize_current_graph(),
        headers={"Content-Disposition": "attachment; filename=graph.json"},
    )


@router.get("/aeropuerto/{iata_id}")
def get_airport_detail(iata_id: str):
    graph = get_graph()
    try:
        vertex = graph.get_vertex(iata_id.upper())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Aeropuerto '{iata_id}' no encontrado")
    return {
        "id": vertex.get_name(),
        "nombre": getattr(vertex, "nombre", vertex.get_name()),
        "ciudad": getattr(vertex, "ciudad", ""),
        "pais": getattr(vertex, "pais", ""),
        "zona_horaria": getattr(vertex, "zona_horaria", ""),
        "es_hub": getattr(vertex, "es_hub", False),
        "costo_alojamiento": getattr(vertex, "costo_alojamiento", 0.0),
        "costo_alimentacion": getattr(vertex, "costo_alimentacion", 0.0),
        "actividades": getattr(vertex, "actividades", []),
        "trabajos": getattr(vertex, "trabajos", []),
        "grado_salida": vertex.get_degree(),
    }


# ── Mutación ───────────────────────────────────────────────────────────

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


# ── Configuración de aeronaves ─────────────────────────────────────────────────
# Spec section 1: "Los datos de costos por km y tiempos por km de cada aeronave
# se pueden sobreescribir en el JSON desde la interfaz gráfica."


@router.get("/configuracion/aeronaves")
def get_config_aeronaves():
    """
    Return current per-aircraft costo_km / tiempo_km in effect for the loaded graph.
    Reads the aircraft_config stored on the first edge found — all edges share the
    same dict instance (unless manually diverged), so this is representative.
    """
    graph = get_graph()
    config: dict = {}
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            if hasattr(edge, "aircraft_config"):
                for name, rates in normalize_aircraft_config(edge.aircraft_config).items():
                    if name not in config:
                        config[name] = dict(rates)
        if config:
            break
    return {"aeronaves": config}


@router.put("/configuracion/aeronaves")
def update_config_aeronaves(payload: dict):
    """
    Override per-aircraft costo_km / tiempo_km at runtime without reloading the JSON.

    Justification: AirportEdge stores aircraft_config as a mutable dict per edge object.
    We iterate all edges in the adjacency list — O(E) — and update each one in place.
    This means subsequent cost/time calculations via get_aircraft_options() will use the
    new rates immediately, with no need to rebuild the graph.

    Body example:
        {
            "Avión Comercial": {"costo_km": 0.15, "tiempo_km": 0.65},
            "Hélice":          {"costo_km": 0.10, "tiempo_km": 2.2}
        }

    Only the aircraft names included in the payload are updated.
    """
    graph = get_graph()
    normalized_payload = normalize_aircraft_config(payload)
    updated: dict = {}
    for vertex in graph.vertices.values():
        for edge in vertex.neighbors:
            if not hasattr(edge, "aircraft_config"):
                continue
            edge.aircraft_config = normalize_aircraft_config(edge.aircraft_config)
            for aircraft_name, new_rates in normalized_payload.items():
                normalized_name = normalize_aircraft_name(aircraft_name)
                current = edge.aircraft_config.get(normalized_name, {})
                edge.aircraft_config[normalized_name] = {
                    "costo_km": float(new_rates.get("costo_km", current.get("costo_km", 0.18))),
                    "tiempo_km": float(new_rates.get("tiempo_km", current.get("tiempo_km", 0.7))),
                }
                updated[normalized_name] = edge.aircraft_config[normalized_name]
    # Mirror into global_config for introspection
    if not hasattr(graph, "global_config"):
        graph.global_config = {}
    graph.global_config.setdefault("aeronaves", {}).update(updated)
    graph.aircraft_config = updated
    return {
        "message": "Configuración de aeronaves actualizada",
        "aeronaves_actualizadas": updated,
        "grafo": serialize_airport_graph(graph),
    }
