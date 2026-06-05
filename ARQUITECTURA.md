# Arquitectura del Proyecto - ProyectoGrafos

## 📋 Descripción General

**ProyectoGrafos** es una API REST construida con **FastAPI** que permite gestionar estructuras de datos de **grafos dirigidos y no dirigidos**. El proyecto implementa patrones de arquitectura por capas (layered architecture) con separación clara de responsabilidades entre modelos de dominio, servicios, repositorios y rutas.

---

## 🛠️ Stack Tecnológico

| Componente | Versión | Propósito |
|-----------|---------|----------|
| **FastAPI** | 0.136.1 | Framework web moderno para construir APIs REST |
| **Uvicorn** | 0.46.0 | Servidor ASGI de producción |
| **Pydantic** | 2.13.4 | Validación de datos y serialización |
| **Python** | 3.10+ | Lenguaje de programación |
| **JSON** | - | Almacenamiento de datos en archivos |

---

## 📁 Estructura del Proyecto

```
ProyectoGrafos/
├── aplication.properties          # Configuración de la aplicación
├── config.py                      # Configuración de rutas y variables globales
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt               # Dependencias del proyecto
├── readme.md                      # Documentación básica
├── ARQUITECTURA.md                # Este documento
│
├── algorithms/                    # 🧮 ALGORITHMS - Algoritmos de grafos
│   ├── dijkstra.py               # Algoritmo de Dijkstra (camino mínimo)
│   ├── bfs_dfs.py                # BFS/DFS (búsqueda y exploración)
│   └── planificacion_avanzada.py # Planificación con costos dinámicos (R3 extendido)
│
├── core/                          # ⭐ CORE - Modelos de dominio
│   ├── edge/
│   │   └── edge.py               # Clase Edge (arista)
│   ├── graph/
│   │   ├── directed_graph.py     # Grafo dirigido
│   │   └── undirected_graph.py   # Grafo no dirigido
│   └── vertex/
│       └── vertex.py              # Clase Vertex (nodo)
│
├── schemas/                       # 📋 SCHEMAS - Validación Pydantic
│   ├── edgeSchema.py             # Validación para aristas
│   ├── grafoSchema.py            # Validación para grafos
│   ├── userSchema.py             # Validación para usuarios
│   └── vertexSchema.py           # Validación para vértices
│
├── repository/                    # 💾 REPOSITORY - Acceso a datos
│   ├── graphRepository.py         # Persistencia de grafos (JSON)
│   ├── userRepository.py          # Persistencia de usuarios (JSON)
│   └── vertexRepository.py        # Persistencia de vértices (JSON)
│
├── service/                       # ⚙️ SERVICE - Lógica de negocio
│   ├── graphService.py           # Servicios de grafos (construcción, serialización)
│   ├── graphState.py             # Gestión centralizada del estado global
│   ├── dijkstraService.py        # Wrapper para Dijkstra multi-criterio
│   ├── dfsService.py             # Wrapper para DFS multi-criterio
│   ├── userService.py            # Servicios de usuarios
│   └── vertexService.py          # Servicios de vértices
│
├── routes/                        # 🌐 ROUTES - Endpoints API
│   ├── grafoRoute.py             # Endpoints para cargar/guardar grafos
│   ├── redRoute.py               # Endpoints para gestionar rutas (bloquear, etc)
│   ├── rutaRoute.py              # Endpoints para búsqueda de rutas (Dijkstra, DFS)
│   ├── userRoute.py              # Endpoints para usuarios
│   └── vertexRoute.py            # Endpoints para vértices
│
└── data/                          # 📊 DATA - Almacenamiento
    ├── edge.json                 # Datos de aristas
    ├── graph.json                # Datos de grafos
    ├── user.json                 # Datos de usuarios
    └── vertex.json               # Datos de vértices
```

---

## 🏗️ Arquitectura en Capas

### 1️⃣ **CAPA DE PRESENTACIÓN (Routes)**
**Ubicación:** `routes/`

- Expone los endpoints REST de la API
- Maneja las peticiones HTTP (GET, POST, PUT, DELETE)
- Valida las peticiones usando esquemas Pydantic
- Delegación a la capa de servicios y algoritmos

**Routers disponibles:**
```
grafoRoute.py   → POST   /grafo/cargar
                  POST   /grafo/cargar-archivo
redRoute.py     → PUT    /grafo/bloquear          (R4 - Bloquear rutas)
rutaRoute.py    → GET    /grafo/ruta              (R2 - Camino mínimo)
                  GET    /grafo/itinerario        (R3 - Máximos destinos)
                  GET    /grafo/planificacion-basica    (R3 - Dos alternativas)
                  GET    /grafo/itinerario-avanzado    (R3 Avanzado - Paso a paso)
                  POST   /grafo/itinerario-avanzado/opciones
                  POST   /grafo/itinerario-avanzado/vuelo
userRoute.py    → Endpoints CRUD de usuarios
vertexRoute.py  → Endpoints CRUD de vértices
```

---

### 2️⃣ **CAPA DE ALGORITMOS (Algorithms)**
**Ubicación:** `algorithms/`

Contiene los algoritmos de teoría de grafos:

#### **Dijkstra** (`dijkstra.py`)
```python
dijkstra(graph, origen: str, criterio: str) → (distancias, previos)
reconstruir_camino(previos, origen, destino) → list[str]
```
- Encuentra camino mínimo entre dos nodos
- Criterios: `distancia`, `tiempo`, `costo`
- Complejidad: O((V + E) log V)
- **Usado en**: R2 - Encontrar ruta más corta

#### **BFS/DFS** (`bfs_dfs.py`)
```python
dfs_mayor_destinos(graph, origen, presupuesto, tiempo_disponible, criterio) → dict
```
- Encuentra ruta que maximiza destinos visitados
- Respeta restricciones de presupuesto/tiempo
- Usa backtracking para explorar todas las opciones
- Complejidad: O(V!) en peor caso, con poda temprana
- **Usado en**: R3 - Itinerario con máximos destinos

#### **Planificación Avanzada** (`planificacion_avanzada.py`) ⭐ NUEVO
```python
planificar_avanzado(graph, origen, presupuesto_inicial) → dict
```
- Planificación con costos dinámicos y trabajos
- Modela alojamiento, alimentación, aeronaves
- Permite trabajar para aumentar presupuesto
- Toma decisiones en tiempo real
- Complejidad: O(V!) con simulación de estado
- **Usado en**: R3 Extendido - Planificación realista

---

### 3️⃣ **CAPA DE SERVICIOS (Service)**
**Ubicación:** `service/`

Contiene la lógica de negocio y orquestación:

#### **graphService.py**
```python
build_graph(data: dict) → Directed_Graph | Undirected_graph
serialize_graph(graph) → dict
serialize_airport_graph(graph) → dict  # Serialización específica para aeropuertos
```

#### **graphState.py** ⭐ NUEVO
```python
get_graph() → Directed_Graph        # Obtiene el grafo en memoria
set_graph(graph) → None              # Establece el grafo en memoria
```
Centraliza la gestión del estado global `current_graph`, evitando múltiples variables globales dispersas.

**Ventajas:**
- Single source of truth para el grafo actual
- Evita inconsistencias entre módulos
- Facilita testing y refactorización futura

#### **dijkstraService.py** ⭐ NUEVO
```python
dijkstra_multi(grafo, salida, filtros) → dict
dijkstra(grafo, salida, filtro) → dict  # (distancia, nodo_anterior)
weight_function(filter, edge) → float   # Selector de criterio
```
Wrapper que encapsula Dijkstra con soporte multi-criterio:
- `filtro=1`: distancia
- `filtro=2`: tiempo
- `filtro=3`: costo

#### **dfsService.py** ⭐ NUEVO
```python
dfs_multi(graph, start, max_weight, filtros) → dict
dfs(graph, start, max_weight, filtro) → list[str]
_weight_function(filter_type, edge) → float
```
Wrapper que encapsula DFS con soporte multi-criterio y límite de peso.

---

### 4️⃣ **CAPA DE PERSISTENCIA (Repository)**
**Ubicación:** `repository/`

- Abstrae el acceso a datos (JSON)
- Proporciona interfaz uniforme para operaciones CRUD
- Implementación actual: Archivos JSON en `data/`

```python
load_graph(path: str) → dict        # Cargar grafo desde JSON
save_graph(path: str, data: dict)    # Guardar grafo en JSON
```

---

### 5️⃣ **CAPA DE DOMINIO (Core)**
**Ubicación:** `core/`

Contiene los modelos de negocio principales:

#### **Vertex (Nodo)**
```python
class Vertex:
    - name: str              # Identificador del nodo
    - available: bool        # Estado de disponibilidad
    - neighbors: list        # Aristas salientes
    
    + get_name()
    + get_neighbors()
    + get_available()
    + set_available()
```

#### **Edge (Arista)**
```python
class Edge:
    - vertex1: Vertex        # Nodo origen
    - vertex2: Vertex        # Nodo destino
    - distance: float        # Distancia
    - time: float            # Tiempo de recorrido
    - cost: float            # Costo
    - available: bool        # Estado (bloqueada o no)
    
    + get_vertex1()
    + get_vertex2()
    + get_distance()
    + get_time()
    + get_cost()
    + set_available()
```

#### **Directed_Graph (Grafo Dirigido)**
```python
class Directed_Graph:
    - vertices: dict         # {nombre: Vertex}
    
    + add_vertex(vertex)
    + add_edge(edge)
    + is_vertex_in(vertex)
    + get_vertex(vertex_name)
```

#### **Undirected_graph (Grafo No Dirigido)**
```python
class Undirected_graph:
    - vertices: dict         # {nombre: Vertex}
    
    # Métodos similares a Directed_Graph
    # Con soporte para aristas bidireccionales
```

---

### 6️⃣ **CAPA DE VALIDACIÓN (Schemas)**
**Ubicación:** `schemas/`

Esquemas Pydantic para validación de entrada/salida:

```python
# Ejemplo: VertexSchema
class VertexPayload(BaseModel):
    name: str                # Requerido

# Ejemplo: EdgeSchema
class EdgePayload(BaseModel):
    vertex1: str             # Nombre del nodo origen
    vertex2: str             # Nombre del nodo destino
    distance: float = 0
    time: float = 0
    cost: float = 0

# Ejemplo: GraphSchema
class GraphPayload(BaseModel):
    directed: bool = True
    vertices: list           # Lista de nombres
    edges: list              # Lista de aristas con propiedades
```

---

## 📊 Flujo de Datos

### Flujo de Carga de Grafo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. FRONTEND/CLIENTE                                         │
│    Envía JSON con estructura del grafo                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ROUTES (grafoRoute.py)                                   │
│    POST /grafo/cargar                                       │
│    - Recibe payload JSON                                    │
│    - Valida con GraphPayload schema                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SERVICE (graphService.py)                                │
│    build_graph(data: dict)                                  │
│    - Crea instancia Directed_Graph o Undirected_graph       │
│    - Itera sobre vértices → crea Vertex objects             │
│    - Itera sobre aristas → crea Edge objects                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CORE (Clases de Dominio)                                 │
│    - Directed_Graph.add_vertex(vertex)                      │
│    - Directed_Graph.add_edge(edge)                          │
│    - Validación de integridad en constructores              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. RESPONSES                                                │
│    - Grafo en memoria (variable global current_graph)       │
│    - Respuesta JSON serializada al cliente                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Ciclo de Vida de una Petición

### Ejemplo: POST /grafo/cargar

**REQUEST:**
```json
{
  "directed": true,
  "vertices": ["A", "B", "C"],
  "edges": [
    {"vertex1": "A", "vertex2": "B", "distance": 5, "time": 10, "cost": 100},
    {"vertex1": "B", "vertex2": "C", "distance": 3, "time": 6, "cost": 50}
  ]
}
```

**PROCESAMIENTO:**

1. **Validación (Pydantic)**
   - Verifica tipos de datos
   - Valida estructura del JSON
   - Convierte a objeto `GraphPayload`

2. **Transformación (Service)**
   - Crea instancia `Directed_Graph`
   - Añade vértices
   - Valida que los vértices existan
   - Crea aristas con atributos

3. **Almacenamiento**
   - Grafo en memoria (variable global `current_graph`)
   - Opcionalmente persiste en `data/graph.json`

4. **Respuesta**
```json
{
  "message": "Grafo cargado correctamente",
  "graph": {
    "directed": true,
    "vertices": ["A", "B", "C"],
    "edges": [...]
  }
}
```

---

## 🔐 Validación y Manejo de Errores

### Validaciones en Edge

```python
if vertex1 is None:
    raise ValueError("Origin vertex not found in graph")
if vertex2 is None:
    raise ValueError("Destination vertex not found in graph")
if distance < 0:
    raise ValueError("Distance must be non-negative")
if time < 0:
    raise ValueError("Time must be non-negative")
if cost < 0:
    raise ValueError("Cost must be non-negative")
```

### Validaciones en Directed_Graph

```python
# No duplicar vértices
if vertex_name in self.vertices:
    raise ValueError("Vertex already in graph")

# Vértices deben existir en el grafo
if vertex_name not in self.vertices:
    raise ValueError(f"Vertex {vertex_name} not in graph")
```

### Manejo HTTP

```python
try:
    current_graph = build_graph(payload.model_dump())
except ValueError as error:
    raise HTTPException(status_code=400, detail=str(error))
except json.JSONDecodeError:
    raise HTTPException(status_code=400, detail="Archivo JSON invalido")
```

---

## 🚀 Configuración e Inicialización

### Configuración (config.py)

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERTEX_JSON_PATH = os.path.join(BASE_DIR, "data", "vertex.json")
GRAPH_JSON_PATH = os.path.join(BASE_DIR, "data", "graph.json")
EDF_JSON_PATH = os.path.join(BASE_DIR, "data", "edge.json")
USER_JSON_PATH = os.path.join(BASE_DIR, "data", "user.json")
```

### Inicialización de la App (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(graph_router, prefix="/grafo", tags=["Grafo"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Vertex"])

@app.get("/")
def home():
    return {"message": "Hola FastAPI"}
```

---

## 📡 Endpoints Principales

### Grafos (`/grafo`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/grafo/cargar` | Cargar grafo desde payload JSON |
| POST | `/grafo/cargar-archivo` | Cargar grafo desde archivo |
| GET | `/grafo/actual` | Obtener grafo actual cargado |
| POST | `/grafo/guardar` | Guardar grafo actual |

### Rutas - Búsqueda de Caminos (`/grafo`)
| Método | Endpoint | Descripción | Algoritmo |
|--------|----------|-------------|-----------|
| GET | `/grafo/ruta?origen=A&destino=B&criterio=distancia` | R2 - Camino mínimo | Dijkstra |
| GET | `/grafo/itinerario?origen=A&presupuesto=1000&tiempo_horas=8` | R3 - Máximos destinos | DFS + Backtracking |
| GET | `/grafo/planificacion-basica?origen=A&presupuesto=1000&tiempo_horas=8` | R3 - Dos alternativas | DFS |
| GET | `/grafo/itinerario-avanzado?origen=A&presupuesto=5000&tiempo_horas=72` | R3 Avanzado - Inicio | DFS + Simulación |
| POST | `/grafo/itinerario-avanzado/opciones` | R3 Avanzado - Opciones | Estado actual |
| POST | `/grafo/itinerario-avanzado/vuelo` | R3 Avanzado - Aplicar decisión | Simulación |

**Parámetros de `/grafo/ruta`:**
- `origen` (str): Código de origen
- `destino` (str): Código de destino  
- `criterio` (str): `distancia` \| `tiempo` \| `costo`

**Respuesta de `/grafo/ruta`:**
```json
{
  "criterio": "distancia",
  "origen": "A",
  "destino": "B",
  "costo_total": 50,
  "camino": ["A", "C", "B"],
  "tramos": [
    {"origen": "A", "destino": "C", "distancia_km": 30, "aeronaves": ["Comercial"]},
    {"origen": "C", "destino": "B", "distancia_km": 20, "aeronaves": ["Regional"]}
  ]
}
```

### Rutas - Gestión (`/grafo`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| PUT | `/grafo/bloquear?origen=A&destino=B` | R4 - Bloquear una ruta |
| GET | `/grafo/disponibles?origen=A` | Obtener rutas disponibles desde A |
| PUT | `/grafo/desbloquear?origen=A&destino=B` | Desbloquear una ruta |

**R4 - Bloquear Ruta:**
```
PUT /grafo/bloquear?origen=MAD&destino=NYC
```
Respuesta:
```json
{
  "message": "Ruta MAD → NYC bloqueada",
  "grafo": { ... }
}
```

### Usuarios (`/users`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/users/crear` | Crear nuevo usuario |
| GET | `/users/{id}` | Obtener usuario por ID |
| PUT | `/users/{id}` | Actualizar usuario |
| DELETE | `/users/{id}` | Eliminar usuario |

### Vértices (`/vertex`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/vertex/crear` | Crear vértice |
| GET | `/vertex/{id}` | Obtener vértice |
| PUT | `/vertex/{id}` | Actualizar vértice |
| DELETE | `/vertex/{id}` | Eliminar vértice |

---

## 📚 Documentación Interactiva

Una vez que la aplicación está en ejecución, accede a:

- **Swagger UI**: `http://127.0.0.1:8000/docs` - Interfaz interactiva
- **ReDoc**: `http://127.0.0.1:8000/redoc` - Documentación alternativa
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json` - Especificación OpenAPI

---

## 🧮 Algoritmos Implementados

### Dijkstra - Camino Mínimo
**Ubicación:** `algorithms/dijkstra.py`

```python
def dijkstra(graph, origen: str, criterio: str) -> tuple[dict, dict]:
    """
    Calcula el camino mínimo desde origen a todos los demás nodos.
    
    Args:
        graph: Directed_Graph
        origen: Código IATA del aeropuerto
        criterio: "distancia" | "tiempo" | "costo"
    
    Returns:
        distancias: {nodo: costo_mínimo}
        previos:    {nodo: nodo_anterior}
    """
```

**Características:**
- Correctitud garantizada para pesos no-negativos ✓
- Retorna distancias y camino óptimo
- Criterios múltiples: distancia, tiempo, costo
- Complejidad: O((V + E) log V) con heap

**Uso:**
```python
distancias, previos = dijkstra(graph, "MAD", "distancia")
camino = reconstruir_camino(previos, "MAD", "NYC")
```

**Caso de uso (R2):**
"Encuentre el camino más corto de Madrid a Nueva York, minimizando distancia/tiempo/costo"

---

### DFS + Backtracking - Máximos Destinos
**Ubicación:** `algorithms/bfs_dfs.py`

```python
def dfs_mayor_destinos(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float,
    criterio: str = "costo",
    excluir_secundarios: bool = False
) -> dict:
    """
    Encuentra la ruta que visita máximos destinos sin exceder límites.
    
    Args:
        graph: Directed_Graph
        origen: Código de origen
        presupuesto: USD disponibles
        tiempo_disponible: minutos disponibles
        criterio: "costo" | "tiempo" (restricción principal)
        excluir_secundarios: filtrar aeropuertos no-hub
    
    Returns:
        {
            "camino": [...],
            "costo_total": 0.0,
            "tiempo_total": 0.0,
            "destinos": 5
        }
    """
```

**Características:**
- Explora todas las rutas posibles con backtracking
- Maximiza destinos visitados, no minimiza costo
- Respeta restricciones de presupuesto/tiempo
- Poda temprana para mejorar rendimiento
- Complejidad: O(V!) en peor caso, O(V) con poda optima

**Uso:**
```python
ruta = dfs_mayor_destinos(
    graph,
    origen="MAD",
    presupuesto=5000,
    tiempo_disponible=480,  # 8 horas
    criterio="costo"
)
```

**Caso de uso (R3):**
"Con 5000 USD y 8 horas disponibles, ¿cuál es la ruta que me permite visitar el máximo número de destinos?"

---

### Planificación Básica - Dos Alternativas
**Ubicación:** `algorithms/bfs_dfs.py`

```python
def planificacion_basica(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: int,
    excluir_secundarios: bool = False,
    aeronaves_permitidas: list | None = None
) → dict
```

**Características:**
- Genera **dos alternativas** automáticamente:
  1. Maximiza destinos respetando **presupuesto**
  2. Maximiza destinos respetando **tiempo**
- Permite seleccionar aeronaves específicas
- Opción para excluir aeropuertos secundarios
- No requiere iteración del usuario

**Respuesta:**
```json
{
  "alternativa_presupuesto": {
    "camino": [...],
    "destinos": 5,
    "costo_total": 4950,
    "tiempo_total": 480
  },
  "alternativa_tiempo": {
    "camino": [...],
    "destinos": 7,
    "costo_total": 5200,
    "tiempo_total": 478
  }
}
```

**Caso de uso (R3 básico):**
"Dame dos opciones de viaje: una optimizada para presupuesto y otra para tiempo, ambas maximizando destinos"

---

### Planificación Avanzada - Costos Dinámicos (Interactiva)
**Ubicación:** `algorithms/planificacion_avanzada.py`

```python
def planificar_avanzado(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: int = 72 * 60
) → dict

def obtener_opciones_planificacion(graph, estado: dict) → dict

def simular_decision_vuelo(
    graph,
    estado: dict,
    destino: str,
    aeronave: str
) → dict
```

**Características:**
- **Costos obligatorios**:
  - Alojamiento: cada 20 horas
  - Alimentación: cada 8 horas
- **Trabajos dinámicos**: Se activan cuando presupuesto < 35% del inicial
- **Decisiones en tiempo real**: DFS con backtracking y simulación
- **Configuración de aeronaves**: Diferentes tipos (Comercial, Regional, Hélice) con costos/tiempos variables
- **Interactividad**: Sistema paso-a-paso con opciones en cada decisión
- Complejidad: O(V!) con poda temprana

**Funciones principales:**
1. `planificar_avanzado()` - Inicia la planificación
2. `obtener_opciones_planificacion()` - Lista decisiones disponibles
3. `simular_decision_vuelo()` - Aplica una decisión y actualiza estado

**Caso de uso (R3 Extendido - Interactivo):**
"Planifica un viaje paso a paso, permitiendo al usuario elegir vuelos, considerar alojamiento/comidas, y trabajar si es necesario para mantener el viaje"

---

## 💾 Persistencia de Datos

### Almacenamiento JSON

El proyecto utiliza archivos JSON en la carpeta `data/` para persistencia:

```
data/
├── vertex.json    # {"vertices": [...]}
├── edge.json      # {"edges": [...]}
├── graph.json     # {"directed": bool, "vertices": [...], "edges": [...]}
└── user.json      # {"users": [...]}
```

**Ejemplo graph.json:**
```json
{
  "directed": true,
  "vertices": ["A", "B", "C"],
  "edges": [
    {
      "vertex1": "A",
      "vertex2": "B",
      "distance": 5,
      "time": 10,
      "cost": 100
    }
  ]
}
```

---

## 🔄 Patrones de Diseño Utilizados

| Patrón | Ubicación | Propósito |
|--------|-----------|----------|
| **Layered Architecture** | Todo el proyecto | Separación de responsabilidades en 6 capas |
| **Repository Pattern** | `repository/` | Abstracción del acceso a datos |
| **Service Layer** | `service/` | Lógica de negocio centralizada |
| **State Management** | `graphState.py` | Single source of truth para grafo global |
| **Builder Pattern** | `graphService.build_graph()` | Construcción de objetos complejos desde datos |
| **Serializer Pattern** | `graphService.serialize_*()` | Conversión objeto ↔ dict/JSON |
| **Strategy Pattern** | Dijkstra vs DFS | Diferentes algoritmos seleccionables |
| **Algorithm Encapsulation** | `algorithms/` | Algoritmos como módulos reutilizables |
| **Dependency Injection** | FastAPI | Inyección de dependencias implícita |
| **Facade Pattern** | `dijkstraService.py`, `dfsService.py` | Simplifica interfaz de algoritmos complejos |
| **State Machine Pattern** | `planificacion_avanzada.py` | Transiciones de estado paso a paso en planning |

---

## 🎯 Decisiones Arquitectónicas

### 1. **Capa de Algoritmos (Nueva)**
   - Módulo independiente `algorithms/` con algoritmos de teoría de grafos
   - Permite reutilización y testing aislado
   - Fácil de mantener y extender
   - Separa lógica algorítmica de lógica de negocio

### 2. **Gestión Centralizada del Estado**
   - Creación de `graphState.py` para centralizar `current_graph`
   - Antes: Variable global dispersa en `grafoRoute.py`
   - Ahora: Funciones `get_graph()` y `set_graph()` como interfaz única
   - Facilita testing, debugging y futuras refactorizaciones

### 3. **Algoritmos Seleccionables**
   - **Dijkstra** para caminos mínimos (R2)
   - **DFS + Backtracking** para maximizar destinos visitados (R3)
   - Cada uno optimizado para su caso de uso

### 4. **Separación de Grafos Dirigidos y No Dirigidos**
   - Clases específicas: `Directed_Graph` y `Undirected_graph`
   - Permite diferente lógica según tipo

### 5. **Persistencia JSON**
   - Simple y sin dependencias externas
   - Fácil de depurar y versionar
   - *Mejora futura:* Migrar a base de datos

### 6. **Validación con Pydantic**
   - Esquemas tipados y autovalidados
   - Documentación automática
   - Seguridad de tipos en tiempo de ejecución

### 8. **Consolidación de Endpoints bajo `/grafo`**
   - Todos los routers (`grafoRoute`, `redRoute`, `rutaRoute`) registrados con prefijo `/grafo`
   - Simplifica navegación de API y facilita documentación
   - Agrupa operaciones relacionadas bajo un solo namespace
   - Endpoints disponibles: `/grafo/cargar`, `/grafo/ruta`, `/grafo/itinerario`, `/grafo/planificacion-basica`, `/grafo/itinerario-avanzado`, `/grafo/bloquear`

### 9. **Planificación Avanzada Interactiva**
   - Sistema paso-a-paso con POST para capturar decisiones del usuario
   - Estado persistente en memoria durante la sesión
   - Flujo de decisiones: elegir vuelo → actualizar presupuesto/tiempo → mostrar opciones siguientes
   - Facilita UIs complejas que requieren múltiples interacciones

---

## 🚦 Próximos Pasos para Implementaciones

### Para agregar nuevas funcionalidades:

1. **Si es un algoritmo de grafos:**
   - Crear archivo en `algorithms/nombre_algoritmo.py`
   - Exportar función principal con interfaz clara
   - Documentar complejidad y caso de uso

2. **Si es una operación con el grafo:**
   - Agregar lógica en `service/graphService.py`
   - Usar `get_graph()` de `graphState.py`
   - Implementar serialización si es necesario

3. **Si es un endpoint REST:**
   - Crear router en `routes/nuevo_nombre_route.py`
   - Definir schema de validación en `schemas/`
   - Delegación clara a service/algoritmos
   - Registrar router en `main.py`

4. **Si necesita persistencia:**
   - Agregar función en `repository/`
   - Usar archivos JSON en `data/`
   - Llamar desde service

5. **Seguir el flujo de datos:**
   ```
   Route → Service → Algorithm/Core → Repository
   ```

### Recomendaciones:
- Mantener la separación en 6 capas
- Validar en múltiples niveles (Schema → Service → Core)
- Documentar algoritmos con docstrings completos
- Usar type hints para claridad
- Reutilizar `graphState.get_graph()` en lugar de variables globales
- Encapsular algoritmos en módulos independientes

---

## 📝 Notas Importantes

### Gestión del Estado
1. **graphState.py centraliza el estado global**: Usar `get_graph()` en lugar de variables globales dispersas ✓
2. *Mejora futura:* Implementar sesiones por usuario para soportar múltiples grafos simultáneos

### Persistencia
1. **JSON es suficiente para desarrollo** en archivos locales
2. *Mejora futura:* Migrar a MongoDB/PostgreSQL para producción
3. *Mejora futura:* Implementar caché (Redis) para operaciones frecuentes

### Algoritmos
1. **Dijkstra**: Garantizado para pesos no-negativos ✓
2. **DFS**: Puede ser lento en grafos muy grandes (considerar heurísticas)
3. **Planificación Avanzada**: Simula decisiones en tiempo real con costos dinámicos
   - Alojamiento cada 20 horas, alimentación cada 8 horas
   - Trabajos disponibles cuando presupuesto < 35%
   - Requiere gestión de estado en memoria
4. *Mejora futura:* Agregar A* con heurística euclidiana para aeropuertos reales

### Escalabilidad
1. Estructura actual es buena base para:
   - Microservicios (separar algoritmos en servicio independiente)
   - Base de datos distribuida
   - Caché distribuido
   - Message queue para operaciones async

### Testing
1. Módulos de `algorithms/` pueden testearse independientemente
2. `graphState.py` facilita inyección de grafos para testing
3. Considerar test fixtures con grafos pequeños para validar correctitud

---

## 📞 Glosario de Términos

| Término | Definición |
|---------|-----------|
| **Vertex/Nodo** | Elemento fundamental del grafo |
| **Edge/Arista** | Conexión entre dos vértices |
| **Grafo Dirigido** | Las aristas tienen dirección (A→B) |
| **Grafo No Dirigido** | Las aristas no tienen dirección (A—B) |
| **Distance** | Distancia entre vértices |
| **Time** | Tiempo de recorrido de una arista |
| **Cost** | Costo asociado a una arista |

---

## 🔀 Flujos de Operaciones Principales

### Flujo 1: Cargar Grafo (R1)

```
POST /grafo/cargar → GraphPayload (Pydantic)
        ↓
grafoRoute.load_graph()
        ↓
graphService.build_graph() ← Crea objetos desde dict
        ↓
graphState.set_graph() ← Almacena en memoria
        ↓
Respuesta: {grafo serializado}
```

### Flujo 2: Camino Mínimo (R2 - Dijkstra)

```
GET /grafo/ruta?origen=A&destino=B&criterio=distancia
        ↓
rutaRoute.get_ruta() ← Valida parámetros
        ↓
graphState.get_graph() ← Obtiene grafo en memoria
        ↓
algorithms.dijkstra.dijkstra() ← Calcula caminos mínimos
        ↓
algorithms.dijkstra.reconstruir_camino() ← Extrae ruta óptima
        ↓
Respuesta: {camino, costo_total, tramos}
```

### Flujo 3: Máximos Destinos (R3 - DFS Simple)

```
GET /grafo/itinerario?origen=A&presupuesto=1000&tiempo_horas=8
        ↓
rutaRoute.get_itinerario() ← Valida restricciones
        ↓
graphState.get_graph() ← Obtiene grafo en memoria
        ↓
algorithms.bfs_dfs.dfs_mayor_destinos() ← Explora todas rutas
        ↓
Respuesta: {camino, destinos_visitados, costo_total, tiempo_total}
```

### Flujo 3b: Planificación Básica (R3 - Dos Alternativas)

```
GET /grafo/planificacion-basica?origen=A&presupuesto=1000&tiempo_horas=8
        ↓
rutaRoute.get_planificacion_basica() ← Valida parámetros
        ↓
graphState.get_graph() ← Obtiene grafo en memoria
        ↓
algorithms.bfs_dfs.planificacion_basica() ← Genera 2 alternativas
        ├─ alternativa_presupuesto: maximiza destinos respetando presupuesto
        └─ alternativa_tiempo: maximiza destinos respetando tiempo
        ↓
Respuesta: {alternativa_presupuesto, alternativa_tiempo}
```

### Flujo 3c: Planificación Avanzada (R3 - Paso a Paso Interactivo)

```
INICIO:
GET /grafo/itinerario-avanzado?origen=A&presupuesto=5000&tiempo_horas=72
        ↓
rutaRoute.get_itinerario_avanzado() ← Inicia simulación
        ↓
algorithms.planificacion_avanzada.planificar_avanzado() 
        ↓
Respuesta: {estado_actual, opciones_disponibles, log}

ITERACIÓN (POST):
POST /grafo/itinerario-avanzado/opciones {estado: {...}}
        ↓
algorithms.planificacion_avanzada.obtener_opciones_planificacion()
        ↓
Respuesta: {vuelos_disponibles, trabajos_disponibles}

POST /grafo/itinerario-avanzado/vuelo {estado, destino, aeronave}
        ↓
algorithms.planificacion_avanzada.simular_decision_vuelo()
        ├─ Actualiza presupuesto y tiempo
        ├─ Verifica alojamiento y comida
        ├─ Evalúa trabajos si presupuesto < 35%
        └─ Retorna nuevo estado
        ↓
Respuesta: {nuevo_estado, opciones_siguientes, log}
```

### Flujo 4: Bloquear Ruta (R4)

```
PUT /grafo/bloquear?origen=A&destino=B
        ↓
redRoute.bloquear_ruta() ← Valida parámetros
        ↓
graphState.get_graph() ← Obtiene grafo en memoria
        ↓
Localiza Edge y ejecuta edge.set_available(False)
        ↓
graphService.serialize_airport_graph() ← Retorna estado actualizado
        ↓
Respuesta: {mensaje, grafo actualizado}
```

---

## 📋 Historial de Cambios

### v2.3 (Junio 3, 2026 - Mejora de Documentación)
✅ **Documentación:**
- Actualización completa del `readme.md` con guía de inicio rápido mejorada
- Resumen ejecutivo con características principales
- Tabla de stack tecnológico y requisitos previos
- Ejemplos de endpoints con solicitudes/respuestas
- Sección de arquitectura resumida con referencia a ARQUITECTURA.md
- Guía de testing y próximas mejoras

✅ **Referencias:**
- README ahora enlaza a ARQUITECTURA.md para documentación completa
- Mejor estructura para desarrolladores nuevos
- Swagger UI y ReDoc destacados como recursos principales

✅ **Mejoras:**
- Documentación más accesible para nuevos desarrolladores
- Ejemplos prácticos de uso de API
- Claridad en arquitectura en capas

---

### v2.2 (Mayo 31, 2026 - Consolidación de Endpoints)
✅ **Consolidaciones:**
- Todos los endpoints ahora bajo prefijo `/grafo` (anteriormente `/ruta` y `/red` separados)
- `redRoute.py` → PUT /grafo/bloquear
- `rutaRoute.py` → GET /grafo/ruta, GET /grafo/itinerario, GET /grafo/planificacion-basica, GET/POST /grafo/itinerario-avanzado

✅ **Nuevos Endpoints (R3 Extended):**
- `GET /grafo/planificacion-basica` - Genera dos alternativas automáticamente (presupuesto vs tiempo)
- `GET /grafo/itinerario-avanzado` - Inicia planning interactivo
- `POST /grafo/itinerario-avanzado/opciones` - Lista decisiones disponibles
- `POST /grafo/itinerario-avanzado/vuelo` - Aplica decisión y actualiza estado

✅ **Mejoras:**
- Consolidación de rutas para API más coherente
- Sistema paso-a-paso para planning avanzado
- 6 endpoints totales en rutaRoute + 1 en redRoute

### v2.1 (Mayo 31, 2026 - Actualización)
✅ **Adiciones:**
- Wrappers de servicios: `dijkstraService.py` y `dfsService.py`
- Algoritmo de planificación avanzada: `planificacion_avanzada.py`
- Soporte para múltiples criterios (distance, time, cost) en servicios
- Costos dinámicos: alojamiento, alimentación, trabajos

✅ **Mejoras:**
- Encapsulación de lógica de peso en funciones `weight_function`
- Soporte para diferentes tipos de aeronaves
- Simulación dinámica de presupuesto y tiempo
- Decisiones inteligentes: trabajos cuando presupuesto baja

### v2.0 (Mayo 31, 2026)
✅ **Adiciones:**
- Capa de algoritmos (`algorithms/`) con Dijkstra y DFS/BFS
- Módulo `graphState.py` para gestión centralizada del estado
- Nuevos routers: `redRoute.py` y `rutaRoute.py`
- Documentación de algoritmos y complejidad
- Flujos de operaciones principales (R2, R3, R4)

✅ **Mejoras:**
- Refactorización: variable global → `graphState.py`
- Arquitectura escalable para futuras extensiones
- Endpoints específicos por dominio (grafo, red, ruta)
- 6 capas bien definidas

### v1.0 (Inicial)
- Arquitectura básica de 5 capas
- CRUD de vértices, aristas y usuarios
- Persistencia JSON

---

*Documento actualizado: Junio 3, 2026*
*Proporcionando contexto arquitectónico completo del proyecto ProyectoGrafos*
