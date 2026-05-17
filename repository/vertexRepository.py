import json
import os
from config import VERTEX_JSON_PATH

def get_airports() -> dict:
    """funcion que carga un un archivo json y lo exporta como un diccionario de vertices
    Returns:        dict: diccionario de vertices cargados
    """
    if not os.path.exists(VERTEX_JSON_PATH):
        raise FileNotFoundError(f"the file with airports data do not exist{VERTEX_JSON_PATH}")
    with open(VERTEX_JSON_PATH, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            raise ValueError(f"the file with airports data is not a valid JSON")


def get_airportById(IATA_code:str) -> dict:
    
    airports= get_airports()
    if IATA_code not in airports:
        raise ValueError(f"the airport with IATA code {IATA_code} do not exist")
    return airports[IATA_code]