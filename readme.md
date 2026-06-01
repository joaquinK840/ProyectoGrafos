# Proyecto FastAPI
dfs
## Requisitos

- Python 3.10 o superior
- pip

---

## Crear entorno virtual

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecutar el servidor

```bash
uvicorn main:app --reload
```

---

## Acceder a la API

### API

```txt
http://127.0.0.1:8000
```

### Swagger UI

```txt
http://127.0.0.1:8000/docs
```

### ReDoc

```txt
http://127.0.0.1:8000/redoc
```