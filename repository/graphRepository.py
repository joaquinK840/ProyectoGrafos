"""
repository/graphRepository.py — JSON network file loader
=========================================================
Provides ``load_graph``, a thin wrapper around ``json.load`` that reads the
flight-network JSON file and returns it as a plain Python dictionary.

The returned dict is handed to the graph-builder in grafoRoute.py, which
iterates the ``"aeropuertos"`` and ``"rutas"`` arrays to construct
``AirportVertex`` and ``AirportEdge`` objects and populate the
``Directed_Graph`` instance.

JSON schema expected
--------------------
{
    "aeropuertos": [ { "iata_id", "nombre", "ciudad", ... }, ... ],
    "rutas":       [ { "origen", "destino", "distancia_km", "aeronaves",
                       "costoBase", "estanciaMinima" }, ... ],
    "configuracion": { "intervaloAlojamiento", "intervaloAlimentacion",
                       "presupuestoMinimoPorc", "limiteSubsidioPorc" }
}
"""

import json


def load_graph(path: str) -> dict:
    """Load a flight-network JSON file and return it as a dictionary.

    Parameters
    ----------
    path : str
        Absolute or relative filesystem path to the ``.json`` network file.

    Returns
    -------
    dict
        Parsed JSON content ready for the graph builder.

    Raises
    ------
    ValueError
        If the file does not exist or contains invalid JSON.
    """
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except json.JSONDecodeError:
        raise ValueError(f"invalid json or format in file: {path}")
