"""
main.py — Application entry point
==================================
Bootstraps the FastAPI application, configures CORS, and mounts all route
routers under their respective URL prefixes.

Routers
-------
- /grafo   : graph upload, airport queries, and all planning endpoints
             (split across grafoRoute, redRoute, and rutaRoute for clarity)
- /vertex  : individual airport lookup by IATA code
- /users   : placeholder user management (not used in core planning logic)

CORS
----
The middleware allows requests from the Vite dev server running on port 5173
(http://localhost:5173 and http://127.0.0.1:5173).  All HTTP methods and
headers are permitted so the React frontend can call every endpoint without
pre-flight issues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.grafoRoute import router as graph_router
from routes.redRoute import router as red_router
from routes.rutaRoute import router as ruta_router
from routes.userRoute import router as user_router
from routes.vertexRoute import router as vertex_router

app = FastAPI(
    title="Flight Network Planning API",
    description=(
        "REST API that models a Latin American airline route network as a "
        "directed weighted graph and exposes planning, pathfinding, and "
        "simulation capabilities."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router registration ───────────────────────────────────────────────────────
# All graph-related routes share the /grafo prefix so the frontend can use a
# single base URL regardless of which sub-feature it is calling.
app.include_router(graph_router, prefix="/grafo", tags=["Graph"])
app.include_router(red_router,   prefix="/grafo", tags=["Network"])
app.include_router(ruta_router,  prefix="/grafo", tags=["Routes & Planning"])
app.include_router(user_router,  prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Airports"])


@app.get("/", tags=["Health"])
def home():
    """Health-check endpoint. Visit /docs for the interactive Swagger UI."""
    return {"message": "API running — visit /docs to explore all endpoints."}
