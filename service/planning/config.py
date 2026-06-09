DEFAULT_INTERVALO_ALOJAMIENTO_HORAS = 20
DEFAULT_INTERVALO_ALIMENTACION_HORAS = 8
DEFAULT_UMBRAL_TRABAJO_PORC = 35
DEFAULT_LIMITE_SUBSIDIO_PORC = 20
DEFAULT_TIEMPO_DISPONIBLE = 72 * 60
DEFAULT_MAX_EXPANSIONES = 20000


def get_config(graph, key, default):
    return getattr(graph, "global_config", {}).get(key, default)


def reglas(graph):
    return {
        "umbral_trabajo_porcentaje": get_config(graph, "presupuestoMinimoPorc", DEFAULT_UMBRAL_TRABAJO_PORC),
        "intervalo_alojamiento_min": get_config(graph, "intervaloAlojamiento", DEFAULT_INTERVALO_ALOJAMIENTO_HORAS) * 60,
        "intervalo_alimentacion_min": get_config(graph, "intervaloAlimentacion", DEFAULT_INTERVALO_ALIMENTACION_HORAS) * 60,
        "limite_subsidio_porcentaje": get_config(graph, "limiteSubsidioPorc", DEFAULT_LIMITE_SUBSIDIO_PORC),
    }


def trabajos_habilitados(graph, estado):
    umbral = get_config(graph, "presupuestoMinimoPorc", DEFAULT_UMBRAL_TRABAJO_PORC) / 100
    return estado["presupuesto_actual"] <= estado["presupuesto_inicial"] * umbral

