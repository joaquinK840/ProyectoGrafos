from fastapi import FastAPI

from routes.grafoRoute import router as graph_router
from routes.redRoute import router as red_router
from routes.rutaRoute import router as ruta_router
from routes.userRoute import router as user_router
from routes.vertexRoute import router as vertex_router
from fastapi.middleware.cors import CORSMiddleware
from routes.redRoute import router as red_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router, prefix="/grafo", tags=["Grafo"])
app.include_router(red_router, prefix="/grafo", tags=["Red"])
app.include_router(ruta_router, prefix="/grafo", tags=["Ruta"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Vertex"])
app.include_router(red_router, prefix="/grafo", tags=["Red"])

@app.get("/")
def home():
    return {"message": "Agrega un /docs en la URL para probar los endpoints de la API"}
