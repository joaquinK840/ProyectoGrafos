# 🏗️ Arquitectura del Proyecto - ProyectoGrafos

## 📋 Descripción General

**ProyectoGrafos** es una **API REST completa** construida con **FastAPI** que implementa una solución integral para gestionar **red aérea (grafos dirigidos)** con soporte para:

✅ **Búsqueda de rutas óptimas** (Dijkstra multi-criterio)  
✅ **Planificación de itinerarios** (DFS con restricciones)  
✅ **Planificación avanzada paso a paso** (Simulación con decisiones)  
✅ **Gestión de rutas bloqueadas** (R4 - Vulnerabilidad)  
✅ **Soporte multi-aeronave** (Opciones de aeronaves por ruta)  

El proyecto implementa **arquitectura por capas (layered architecture)** con separación clara de responsabilidades entre **algoritmos, servicios, persistencia, validación y rutas**.

---

## 🛠️ Stack Tecnológico

| Componente | Versión | Propósito |
|-----------|---------|----------|
| **FastAPI** | 0.136.1 | Framework web moderno, alto rendimiento |
| **Uvicorn** | 0.46.0 | Servidor ASGI de producción |
| **Pydantic** | 2.13.4 | Validación y serialización de datos |
| **Python** | 3.10+ | Lenguaje de programación |
| **JSON** | - | Persistencia de datos en archivos |
| **CORS** | - | Middleware para solicitudes cross-origin |

---

## 📁 Estructura del Proyecto

```
ProyectoGrafos/
├── aplication.properties          # Configuración de la aplicación
├── config.py                      # Configuración de rutas y variables globales
├── main.py                        # Punto de entrada, registra routers y middleware
├── requirements.txt               # Dependencias: FastAPI, Uvicorn, Pydantic, etc.
├── readme.md                      # Documentación básica del proyecto
├── ARQUITECTURA.md                # Este documento
│
├── 🧮 algorithms/                 # ALGORITMOS DE GRAFOS
│   ├── dijkstra.py               # Dijkstra: camino mínimo (O((V+E)logV))
│   ├── bfs_dfs.py                # DFS: máximos destinos con restricciones
│   └── planificacion_avanzada.py # Planificación avanzada con trabajos y alojamiento
│
├── ⭐ core/                       # MODELOS DE DOMINIO
│   ├── edge/
│   │   ├── edge.py               # Clase Edge base
│   │   └── airport_edge.py       # Edge especializado para red aérea
│   ├── graph/
│   │   ├── directed_graph.py     # Grafo dirigido (red aérea)
│   │   └── undirected_graph.py   # Grafo no dirigido (genérico)
│   └── vertex/
│       ├── vertex.py             # Clase Vertex base
│       └── airport_vertex.py     # Vertex especializado para aeropuertos
│
├── 📋 schemas/                    # VALIDACIÓN PYDANTIC
│   ├── edgeSchema.py             # Schema para aristas
│   ├── grafoSchema.py            # Schema para grafos
│   ├── dfsSchema.py              # Schema para DFS multi-criterio
│   ├── dijkstraSchema.py         # Schema para Dijkstra multi-criterio
│   ├── userSchema.py             # Schema para usuarios
│   └── vertexSchema.py           # Schema para vértices
│
├── 💾 repository/                # CAPA DE PERSISTENCIA
│   ├── graphRepository.py        # CRUD para grafos (JSON)
│   ├── userRepository.py         # CRUD para usuarios (JSON)
│   └── vertexRepository.py       # CRUD para vértices (JSON)
│
├── ⚙️ service/                    # LÓGICA DE NEGOCIO
│   ├── graphService.py           # Construcción y serialización de grafos
│   ├── graphState.py             # 🔴 NUEVO: Gestión centralizada del estado
│   ├── dijkstraService.py        # 🔴 NUEVO: Wrapper multi-criterio para Dijkstra
│   ├── dfsService.py             # 🔴 NUEVO: Wrapper multi-criterio para DFS
│   ├── userService.py            # Servicios de usuarios
│   └── vertexService.py          # Servicios de vértices
│
├── 🌐 routes/                     # ENDPOINTS REST
│   ├── grafoRoute.py             # GET/POST: cargar, guardar, obtener grafos
│   ├── redRoute.py               # PUT: bloquear/desbloquear rutas (R4)
│   ├── rutaRoute.py              # GET: búsqueda de rutas (R2, R3, R3-Avanzado)
│   ├── userRoute.py              # CRUD: crear, leer, actualizar, eliminar usuarios
│   └── vertexRoute.py            # CRUD: crear, leer, actualizar, eliminar vértices
│
└── 📊 data/                       # ALMACENAMIENTO JSON
    ├── edge.json                 # Datos de aristas (red aérea LATAM)
    ├── graph.json                # Datos de grafos completos
    ├── red_aerea_latam.json      # Datos específicos red LATAM
    ├── user.json                 # Datos de usuarios
    └── vertex.json               # Datos de vértices/aeropuertos
```

---

## 🏗️ Arquitectura en Capas

### 1️⃣ **CAPA DE PRESENTACIÓN (Routes)**
**Ubicación:** `routes/`

Expone los **endpoints REST** de la API FastAPI. Cada router:
- ✅ Valida peticiones con esquemas **Pydantic**
- ✅ Maneja errores HTTP (400, 404, 500)
- ✅ Serializa respuestas a JSON
- ✅ Delega lógica a capas inferiores

**Routers registrados en `main.py`:**
```python
app.include_router(graph_router, prefix="/grafo", tags=["Grafo"])
app.include_router(red_router, prefix="/grafo", tags=["Red"])
app.include_router(ruta_router, prefix="/grafo", tags=["Ruta"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Vertex"])
```

---

### 2️⃣ **CAPA DE ALGORITMOS (Algorithms)**
**Ubicación:** `algorithms/`

Implementa los **algoritmos de teoría de grafos** requeridos:

#### 🔹 **Dijkstra** (`dijkstra.py`) - R2: Camino Mínimo
```python
dijkstra(graph, origen: str, criterio: str, destino: str, ...) 
  → (distancias: dict, previos: dict)

reconstruir_camino(previos, origen, destino) → list[str]
```

**Características:**
- ✅ Encuentra camino mínimo en grafos ponderados
- ✅ Criterios múltiples: `distancia`, `tiempo`, `costo`, `combinado`
- ✅ Soporte para excluir aeropuertos secundarios
- ✅ Filtrado por tipo de aeronave permitida
- ✅ Complejidad: **O((V + E) log V)** con heap binario

**Uso:**
```python
distancias, previos = dijkstra(
    graph, 
    origen="MAD", 
    criterio="distancia",
    destino="NYC",
    excluir_secundarios=False,
    aeronaves_permitidas=None
)
camino = reconstruir_camino(previos, "MAD", "NYC")
```

**R2 - Caso de Uso:**  
"¿Cuál es la ruta más corta desde Madrid a Nueva York minimizando [distancia/tiempo/costo]?"

---

#### 🔹 **DFS + Backtracking** (`bfs_dfs.py`) - R3: Máximos Destinos

**Función Principal:**
```python
dfs_mayor_destinos(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float,
    criterio: str = "costo",
    excluir_secundarios: bool = False
) → dict
```

**Características:**
- ✅ Explora **todas las rutas posibles** con backtracking
- ✅ Maximiza destinos visitados (no minimiza costo)
- ✅ Respeta restricciones: presupuesto y tiempo
- ✅ Poda temprana: elimina ramas no prometedoras
- ✅ Complejidad: **O(V!)** peor caso, O(V) con poda óptima

**Respuesta:**
```json
{
  "camino": ["MAD", "PAR", "LON", "AMS"],
  "destinos": 4,
  "costo_total": 4500.50,
  "tiempo_total": 480.0,
  "tramos": [...]
}
```

**R3 - Caso de Uso:**  
"Con 5000 USD y 8 horas, ¿qué ruta me permite visitar el máximo número de destinos?"

---

#### 🔹 **Planificación Básica** (`bfs_dfs.py`) - R3: Dos Alternativas

```python
planificacion_basica(
    graph,
    origen: str,
    presupuesto: float,
    tiempo_disponible: float
) → dict
```

Genera **dos alternativas de rutas**:
1. **Ruta A:** Maximiza destinos con DFS
2. **Ruta B:** Alternativa de diversidad

**R3 - Caso de Uso:**  
"Proporcione dos alternativas viables de itinerarios."

---

#### 🔹 **Planificación Avanzada** (`planificacion_avanzada.py`) - R3 Extendido ⭐ NUEVO

**Flujo Paso a Paso:**
```python
planificar_avanzado(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float = 72*60
) → dict  # Estado inicial con opciones disponibles

simular_decision_vuelo(graph, estado, destino) → dict  # Tomar vuelo
simular_decision_trabajo(graph, estado, ciudad) → dict  # Trabajar
simular_decision_actividad(graph, estado, actividad) → dict  # Actividad
```

**Características:**
- ✅ Modela **costo de vida realista:** alojamiento, alimentación, transporte
- ✅ Permite **trabajar para aumentar presupuesto** (realismo)
- ✅ Toma decisiones **en tiempo real** (no planificación a priori)
- ✅ Genera **reporte final** con estadísticas
- ✅ Soporte para actividades (playas, museos, montañas)

**Flujo:**
```
1. planificar_avanzado()        → Estado inicial + opciones
2. obtener_opciones()           → Vuelos, trabajos, actividades disponibles
3. simular_decision_vuelo()     → Usuario elige destino
4. Repetir 2-3 hasta fin o presupuesto agotado
5. generar_reporte_final()      → Estadísticas del viaje
```

**Constantes de Negocio:**
- DEFAULT_INTERVALO_ALOJAMIENTO_HORAS = 20
- DEFAULT_INTERVALO_ALIMENTACION_HORAS = 8
- DEFAULT_UMBRAL_TRABAJO_PORC = 35 (%)
- DEFAULT_LIMITE_SUBSIDIO_PORC = 20 (%)
- DEFAULT_TIEMPO_DISPONIBLE = 72 * 60 (minutos)

**R3 Avanzado - Caso de Uso:**  
"Planifique un viaje realista con alojamiento, comidas y oportunidades de trabajo."

**Flujo Automático:**
```python
planificar_avanzado_automatico(
    graph,
    origen: str,
    presupuesto_inicial: float,
    tiempo_disponible: float = 72*60,
    max_expansiones: int = 20000  # Límite para evitar timeout
) → dict  # Mejor itinerario encontrado
```

Busca automáticamente el **mejor itinerario** usando DFS acotado:
- Criterio: Maximizar destinos → Minimizar gasto → Minimizar tiempo

---

### 3️⃣ **CAPA DE SERVICIOS (Service)**
**Ubicación:** `service/`

Encapsula **lógica de negocio** y **orquestación**:

#### **graphService.py**
```python
build_graph(data: dict) → Directed_Graph | Undirected_Graph
serialize_graph(graph) → dict
serialize_airport_graph(graph) → dict  # Serialización específica LATAM
```

- Construye grafos desde JSON
- Valida integridad de vértices y aristas
- Serializa grafos para respuestas HTTP

---

#### **graphState.py** ⭐ NUEVO - Gestión de Estado Central
```python
get_graph() → Directed_Graph        # Obtiene grafo en memoria
set_graph(graph) → None              # Establece grafo en memoria
```

**Propósito:**
- 🎯 **Single source of truth** para el grafo actual
- 🎯 Evita múltiples variables globales dispersas
- 🎯 Facilita testing y refactorización

**Ventajas:**
```python
# ❌ ANTES: Variables globales dispersas
current_graph = None  # En rutaRoute.py
graph = None          # En grafoRoute.py

# ✅ DESPUÉS: Gestión centralizada
from service.graphState import get_graph, set_graph
graph = get_graph()
```

---

#### **dijkstraService.py** ⭐ NUEVO - Wrapper Multi-Criterio
```python
dijkstra_multi(grafo, salida, filtros) → dict
dijkstra(grafo, salida, filtro) → dict  # (distancia, nodo_anterior)
weight_function(filter, edge) → float   # Selector de criterio
```

Encapsula Dijkstra con **soporte multi-criterio**:
- Filtro 1: Distancia (km)
- Filtro 2: Tiempo (minutos)
- Filtro 3: Costo (USD)

---

#### **dfsService.py** ⭐ NUEVO - Wrapper Multi-Criterio
```python
dfs_multi(graph, start, max_weight, filtros) → dict
dfs(graph, start, max_weight, filtro) → list[str]
_weight_function(filter_type, edge) → float
```

Encapsula DFS con **soporte multi-criterio y límite de peso**.

---

### 4️⃣ **CAPA DE PERSISTENCIA (Repository)**
**Ubicación:** `repository/`

Abstrae el **acceso a datos** (JSON). Proporciona interfaz uniforme para operaciones CRUD:

```python
# graphRepository.py
load_graph(path: str) → dict        # Cargar grafo desde JSON
save_graph(path: str, data: dict)   # Guardar grafo en JSON
```

**Implementación actual:** Archivos JSON en `data/`  
**Evolución futura:** Migrar a BD (PostgreSQL, MongoDB)

---

### 5️⃣ **CAPA DE DOMINIO (Core)**
**Ubicación:** `core/`

Contiene los **modelos de negocio** principales:

#### **Vertex (Nodo)**
```python
class Vertex:
    name: str              # Código único (ej: "MAD", "NYC")
    available: bool        # Estado de disponibilidad
    neighbors: list[Edge]  # Aristas salientes
    
    + get_name() → str
    + get_neighbors() → list[Edge]
    + get_available() → bool
    + set_available(bool)
```

#### **Airport_Vertex** ⭐ NEW (Especialización)
```python
class AirportVertex(Vertex):
    iata_code: str        # Código IATA
    city: str             # Ciudad
    country: str          # País
    is_hub: bool          # ¿Es hub principal?
```

---

#### **Edge (Arista)**
```python
class Edge:
    vertex1: Vertex        # Nodo origen
    vertex2: Vertex        # Nodo destino
    distance: float        # Distancia (km)
    time: float            # Tiempo de vuelo (min)
    cost: float            # Costo (USD)
    available: bool        # ¿Está disponible/bloqueada?
    
    + get_vertex1() → Vertex
    + get_vertex2() → Vertex
    + get_distance() → float
    + get_time() → float
    + get_cost() → float
    + set_available(bool)
    + get_aircraft_options() → list[dict]  # Aeronaves disponibles
```

#### **Airport_Edge** ⭐ NEW (Especialización)
```python
class AirportEdge(Edge):
    aircraft: list[dict]  # Opciones de aeronaves
                          # [{"nombre": "Boeing777", "tiempo": 600, ...}]
    
    + get_aircraft_options() → list[dict]
    + get_aeronaves() → list[str]
```

---

#### **Directed_Graph (Grafo Dirigido)**
```python
class Directed_Graph:
    vertices: dict[str, Vertex]  # {nombre: Vertex}
    
    + add_vertex(vertex: Vertex)
    + add_edge(edge: Edge)
    + is_vertex_in(vertex_name: str) → bool
    + get_vertex(vertex_name: str) → Vertex | None
```

---

#### **Undirected_Graph (Grafo No Dirigido)**
```python
class Undirected_Graph(Directed_Graph):
    # Métodos iguales a Directed_Graph
    # Con soporte para aristas bidireccionales
```

---

### 6️⃣ **CAPA DE VALIDACIÓN (Schemas)**
**Ubicación:** `schemas/`

Esquemas **Pydantic** para validación de entrada/salida HTTP:

```python
# vertexSchema.py
class VertexPayload(BaseModel):
    name: str              # Requerido

# edgeSchema.py  
class EdgePayload(BaseModel):
    vertex1: str
    vertex2: str
    distance: float = 0.0
    time: float = 0.0
    cost: float = 0.0

# grafoSchema.py
class GraphPayload(BaseModel):
    directed: bool = True
    vertices: list[str]
    edges: list[EdgePayload]

# dijkstraSchema.py ⭐ NEW
class DijkstraRequest(BaseModel):
    criterio: str  # "distancia" | "tiempo" | "costo"

# dfsSchema.py ⭐ NEW
class DFSRequest(BaseModel):
    presupuesto: float
    tiempo_horas: float
    criterio: str = "costo"
```
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
┌──────────────────────────────────────────────────────────────────┐
│ 1. CLIENTE (Frontend / Postman)                                  │
│    POST /grafo/cargar                                            │
│    Payload: { "directed": true, "vertices": [...], ... }        │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. ROUTES LAYER (rutaRoute.py / grafoRoute.py)                   │
│    - Recibe payload JSON                                         │
│    - Valida con schema Pydantic (GraphPayload)                   │
│    - Maneja errores HTTP (400, 404, 500)                        │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. SERVICE LAYER (graphService.py + graphState.py)               │
│    build_graph(data: dict)                                       │
│    - Crea instancia Directed_Graph o Undirected_Graph            │
│    - Itera sobre vértices → crea Vertex/AirportVertex objects    │
│    - Itera sobre aristas → crea Edge/AirportEdge objects         │
│    - Valida integridad                                           │
│    set_graph(grafo) → Almacena en estado central                 │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. DOMAIN LAYER (core/)                                          │
│    - Directed_Graph.add_vertex(vertex)                           │
│    - Directed_Graph.add_edge(edge)                               │
│    - Validación de integridad en constructores                   │
│    - Nexo entre vértices y aristas                               │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. PERSISTENCE LAYER (repository/)                               │
│    graphRepository.save_graph(path, data)                        │
│    - Persiste grafo en data/graph.json                           │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE (HTTP JSON)                                          │
│    200 OK                                                        │
│    { "message": "Grafo cargado", "graph": {...} }               │
└──────────────────────────────────────────────────────────────────┘
```

---

### Flujo de Búsqueda de Ruta (R2: Dijkstra)

```
┌──────────────────────────────────────────────────────────────────┐
│ GET /grafo/ruta?origen=MAD&destino=NYC&criterio=distancia       │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. VALIDATION                                                    │
│    - Verificar que origen y destino existen en el grafo         │
│    - Validar criterio ∈ {distancia, tiempo, costo, combinado}  │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. ALGORITHM (dijkstra.py)                                       │
│    dijkstra(graph, origen, criterio, destino, ...)              │
│    Retorna:                                                      │
│      - distancias = {MAD: 0, PAR: 500, LON: 800, NYC: 1200}     │
│      - previos = {MAD: None, PAR: MAD, LON: PAD, NYC: LON}      │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. RECONSTRUCT PATH                                              │
│    camino = reconstruir_camino(previos, MAD, NYC)               │
│    camino = [MAD, PAR, LON, NYC]                                │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. BUILD DETAILS                                                 │
│    Para cada tramo (vi, vi+1):                                  │
│      - Buscar Edge(vi, vi+1)                                    │
│      - Elegir aeronave según criterio                           │
│      - Acumular distancia, tiempo, costo                        │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                      │
│    {                                                             │
│      "criterio": "distancia",                                   │
│      "origen": "MAD",                                           │
│      "destino": "NYC",                                          │
│      "distancia_total": 9500,                                   │
│      "tiempo_total": 1380,                                      │
│      "costo_total": 2450.75,                                    │
│      "camino": ["MAD", "PAR", "LON", "NYC"],                   │
│      "tramos": [                                                │
│        {                                                         │
│          "origen": "MAD",                                       │
│          "destino": "PAR",                                      │
│          "aeronave": "Boeing 787",                              │
│          "distancia_km": 1050,                                  │
│          "tiempo_tramo": 300,                                   │
│          "tiempo_acumulado": 300,                               │
│          "costo_tramo": 350.25,                                 │
│          "costo_acumulado": 350.25                              │
│        },                                                        │
│        ...                                                       │
│      ]                                                           │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📡 Endpoints REST

### 📋 Cargar/Guardar Grafos (`grafoRoute.py`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| **POST** | `/grafo/cargar` | Cargar grafo desde payload JSON |
| **POST** | `/grafo/cargar-archivo` | Cargar grafo desde archivo JSON |
| **GET** | `/grafo/actual` | Obtener grafo actual cargado |
| **POST** | `/grafo/guardar` | Guardar grafo actual en archivo |
| **GET** | `/grafo/serializacion` | Obtener serialización en memoria |

---

### 🛫 Búsqueda de Rutas - R2, R3, R3-Avanzado (`rutaRoute.py`)

#### **R2: Camino Mínimo - Dijkstra**
```
GET /grafo/ruta
    ?origen=MAD
    &destino=NYC
    &criterio=distancia
    &excluir_secundarios=false
    &aeronaves=Boeing777,Airbus380
```

**Parámetros:**
- `origen` (str): Código IATA de origen
- `destino` (str): Código IATA de destino
- `criterio` (str): `distancia` | `tiempo` | `costo` | `combinado`
- `excluir_secundarios` (bool): Omitir aeropuertos no-hub
- `aeronaves` (list): Filtrar por tipo de aeronave

**Respuesta:** Ver sección "Flujo de Búsqueda de Ruta (R2)"

---

#### **R3: Máximos Destinos - DFS**
```
GET /grafo/itinerario
    ?origen=MAD
    &presupuesto=5000
    &tiempo_horas=8
    &criterio=costo
    &excluir_secundarios=false
```

**Parámetros:**
- `origen` (str): Código IATA de origen
- `presupuesto` (float): USD disponibles
- `tiempo_horas` (float): Horas disponibles
- `criterio` (str): `costo` | `tiempo` (restricción principal)
- `excluir_secundarios` (bool): Omitir aeropuertos no-hub

**Respuesta:**
```json
{
  "camino": ["MAD", "PAR", "LON", "AMS", "VIE"],
  "destinos": 5,
  "costo_total": 4850.50,
  "tiempo_total": 420.0,
  "tramos": [...]
}
```

---

#### **R3: Planificación Básica - Dos Alternativas**
```
GET /grafo/planificacion-basica
    ?origen=MAD
    &presupuesto=5000
    &tiempo_horas=8
```

Retorna dos alternativas de itinerarios viables.

**Respuesta:**
```json
{
  "alternativa_1": {
    "camino": [...],
    "destinos": 5,
    "costo_total": 4500.0
  },
  "alternativa_2": {
    "camino": [...],
    "destinos": 4,
    "costo_total": 3800.0
  }
}
```

---

#### **R3 Avanzado: Planificación Paso a Paso** ⭐ NEW
```
GET /grafo/itinerario-avanzado
    ?origen=MAD
    &presupuesto=5000
    &tiempo_horas=72
```

**Flujo:**
1. **Retorna estado inicial + opciones disponibles**
```json
{
  "estado": {
    "aeropuerto_actual": "MAD",
    "presupuesto_disponible": 5000,
    "tiempo_disponible_min": 4320,
    "visitados": ["MAD"],
    "total_gastado": 0
  },
  "opciones": {
    "vuelos": [...],
    "trabajos": [...],
    "actividades": [...]
  }
}
```

2. **Usuario toma decisión (vuelo, trabajo, actividad)**
```
POST /grafo/itinerario-avanzado/vuelo
{
  "estado": {...},
  "destino": "PAR",
  "aeronave": "Boeing787"
}
```

3. **Sistema actualiza estado y retorna nuevas opciones**

4. **Generar reporte final**
```
POST /grafo/itinerario-avanzado/reporte
{
  "estado": {...}
}
```

**Reporte Final:**
```json
{
  "ciudad_inicio": "MAD",
  "ciudad_final": "VIE",
  "ciudades_visitadas": ["MAD", "PAR", "LON", "AMS", "VIE"],
  "total_ciudades": 5,
  "presupuesto_inicial": 5000,
  "presupuesto_restante": 245.50,
  "total_gastado": 4754.50,
  "tiempo_inicial_horas": 72,
  "tiempo_utilizado_horas": 62.5,
  "tiempo_restante_horas": 9.5,
  "detalles_vuelos": [...],
  "detalles_trabajos": [...],
  "detalles_actividades": [...]
}
```

---

### 🚫 Gestión de Rutas - R4 (`redRoute.py`)

#### **Bloquear Ruta**
```
PUT /grafo/bloquear
    ?origen=MAD
    &destino=NYC
```

Bloquea la conexión MAD → NYC.

**Respuesta:**
```json
{
  "message": "Ruta MAD → NYC bloqueada",
  "grafo": {...}
}
```

---

#### **Desbloquear Ruta**
```
PUT /grafo/desbloquear
    ?origen=MAD
    &destino=NYC
```

Desbloquea la conexión MAD → NYC.

---

#### **Rutas Disponibles desde Origen**
```
GET /grafo/disponibles
    ?origen=MAD
```

Retorna todas las rutas disponibles (no bloqueadas) desde MAD.

---

### 👥 Usuarios (`userRoute.py`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/users/crear` | Crear nuevo usuario |
| GET | `/users/{id}` | Obtener usuario por ID |
| PUT | `/users/{id}` | Actualizar usuario |
| DELETE | `/users/{id}` | Eliminar usuario |
| GET | `/users` | Listar todos los usuarios |

---

### ✈️ Vértices/Aeropuertos (`vertexRoute.py`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/vertex/crear` | Crear vértice |
| GET | `/vertex/{id}` | Obtener vértice por ID |
| PUT | `/vertex/{id}` | Actualizar vértice |
| DELETE | `/vertex/{id}` | Eliminar vértice |
| GET | `/vertex` | Listar todos los vértices |

---

## 🔐 Validación y Manejo de Errores

### Validaciones en Edge

```python
if vertex1 is None:
    raise ValueError("Origin vertex not found in graph")
if vertex2 is None:
    raise ValueError("Destination vertex not found in graph")
if distance < 0 or time < 0 or cost < 0:
    raise ValueError("Distance, time, and cost must be non-negative")
```

---

### Validaciones en Directed_Graph

```python
# No duplicar vértices
if vertex_name in self.vertices:
    raise ValueError("Vertex already exists in graph")

# Vértices referenciados deben existir
if edge.get_vertex1().get_name() not in self.vertices:
    raise ValueError("Origin vertex not in graph")
if edge.get_vertex2().get_name() not in self.vertices:
    raise ValueError("Destination vertex not in graph")
```

---

### Manejo HTTP Centralizado

```python
try:
    # Lógica de negocio
    graph = build_graph(payload.model_dump())
    set_graph(graph)
    return {"message": "Grafo cargado", "graph": serialize_graph(graph)}
    
except ValueError as error:
    raise HTTPException(status_code=400, detail=str(error))
except json.JSONDecodeError:
    raise HTTPException(status_code=400, detail="JSON inválido")
except Exception as error:
    raise HTTPException(status_code=500, detail="Error interno del servidor")
```

---

## 🚀 Configuración e Inicialización

### Configuración (`config.py`)

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas de datos
VERTEX_JSON_PATH = os.path.join(BASE_DIR, "data", "vertex.json")
GRAPH_JSON_PATH = os.path.join(BASE_DIR, "data", "graph.json")
EDGE_JSON_PATH = os.path.join(BASE_DIR, "data", "edge.json")
USER_JSON_PATH = os.path.join(BASE_DIR, "data", "user.json")
RED_AEREA_LATAM_PATH = os.path.join(BASE_DIR, "data", "red_aerea_latam.json")
```

---

### Inicialización de App (`main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ProyectoGrafos API",
    description="API para gestión de red aérea y búsqueda de rutas óptimas",
    version="2.0.0"
)

# Middleware CORS - Permite solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Cualquier origen
    allow_credentials=True,       # Con credenciales
    allow_methods=["*"],          # Todos los métodos
    allow_headers=["*"],          # Todos los headers
)

# Registrar routers
app.include_router(graph_router, prefix="/grafo", tags=["Grafo"])
app.include_router(red_router, prefix="/grafo", tags=["Red"])
app.include_router(ruta_router, prefix="/grafo", tags=["Ruta"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(vertex_router, prefix="/vertex", tags=["Vertex"])

@app.get("/")
def home():
    return {
        "message": "🌍 ProyectoGrafos API",
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc"
    }
```

---

## 📚 Documentación Interactiva

Una vez que la aplicación está en ejecución:

- **Swagger UI**: `http://127.0.0.1:8000/docs` - Interfaz interactiva para probar endpoints
- **ReDoc**: `http://127.0.0.1:8000/redoc` - Documentación alternativa
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json` - Especificación OpenAPI

---

## 📊 Algoritmos Implementados

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
