from service.planning.config import DEFAULT_LIMITE_SUBSIDIO_PORC, get_config


def opcion_con_subsidio(graph, edge, option):
    option = dict(option)
    option["km_subsidiados"] = 0
    if not edge.is_subsidiada():
        return option

    limite = get_config(graph, "limiteSubsidioPorc", DEFAULT_LIMITE_SUBSIDIO_PORC) / 100
    km_subsidiados = round(edge.get_distance() * limite, 2)
    km_cobrados = max(0, edge.get_distance() - km_subsidiados)
    option["costo"] = round(km_cobrados * option["costo_km"], 2)
    option["km_subsidiados"] = km_subsidiados
    return option

