from fastapi import FastAPI

from routes.grafoRoute import router as graph_router
from routes.userRoute import router as user_router
from routes.vertexRoute import router as vertex_router
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Vertex"])

@app.get("/")
def home():
    return {"message": "Hola FastAPI"}
