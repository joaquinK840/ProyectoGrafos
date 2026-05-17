import json
def load_graph(path:str) -> dict:
    """funcion que carga un un archivo json y lo exporta como un diccionario
    Args:        path (str): ruta del archivo json a cargar
    Returns:        dict: diccionario con la estructura del grafo cargado
    """
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError:
        raise ValueError(f"invalid json or format in file: {path}")