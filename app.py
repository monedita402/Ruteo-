import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


# ============================================================
# CONFIGURACIÓN STREAMLIT
# ============================================================

st.set_page_config(
    page_title="CVRP - Expreso de la Montaña",
    layout="wide"
)

st.title("🚚 Optimización de Rutas - Expreso de la Montaña")
st.subheader("Modelo CVRP para logística de última milla en el Valle de Aburrá")


# ============================================================
# FUNCIÓN DISTANCIA
# ============================================================

def calcular_distancia_euclidiana(coord1, coord2):

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    distancia_grados = math.sqrt(
        delta_lat**2 + delta_lon**2
    )

    distancia_metros = distancia_grados * 111000

    return int(distancia_metros)


# ============================================================
# MODELO DE DATOS
# ============================================================

def crear_modelo_datos():

    datos = {}

    datos['coordenadas'] = [

        [6.151, -75.615],
        [6.210, -75.571],
        [6.173, -75.583],
        [6.172, -75.609],
        [6.333, -75.558],
        [6.243, -75.594]

    ]

    datos['nombres_nodos'] = [

        "CEDI Sabaneta",
        "El Poblado",
        "Envigado",
        "Itagüí",
        "Bello",
        "Laureles"

    ]

    datos['demandas'] = [

        0,
        1800,
        1200,
        1500,
        2200,
        900

    ]

    datos['capacidades_vehiculos'] = [

        4000,
        4000

    ]

    datos['num_vehiculos'] = 2

    datos['deposito'] = 0

    matriz_distancias = []

    num_puntos = len(datos['coordenadas'])

    for i in range(num_puntos):

        fila = []

        for j in range(num_puntos):

            distancia = calcular_distancia_euclidiana(
                datos['coordenadas'][i],
                datos['coordenadas'][j]
            )

            fila.append(distancia)

        matriz_distancias.append(fila)

    datos['matriz_distancias'] = matriz_distancias

    return datos


# ============================================================
# EXTRAER RUTAS
# ============================================================

def extraer_rutas(data, manager, routing, solution):

    rutas = []

    for vehiculo_id in range(data['num_vehiculos']):

        index = routing.Start(vehiculo_id)

        ruta = []

        distancia_total = 0

        while not routing.IsEnd(index):

            nodo = manager.IndexToNode(index)

            ruta.append(nodo)

            indice_anterior = index

            index = solution.Value(
                routing.NextVar(index)
            )

            distancia_total += routing.GetArcCostForVehicle(
                indice_anterior,
                index,
                vehiculo_id
            )

        ruta.append(manager.IndexToNode(index))

        rutas.append({

            'vehiculo': vehiculo_id + 1,
            'ruta': ruta,
            'distancia': distancia_total

        })

    return rutas


# ============================================================
# RESOLVER MODELO
# ============================================================

def resolver_modelo():

    datos = crear_modelo_datos()

    manager = pywrapcp.RoutingIndexManager(

        len(datos['matriz_distancias']),
        datos['num_vehiculos'],
        datos['deposito']

    )

    routing = pywrapcp.RoutingModel(manager)

    def distancia_callback(desde_index, hacia_index):

        desde_nodo = manager.IndexToNode(desde_index)

        hacia_nodo = manager.IndexToNode(hacia_index)

        return datos['matriz_distancias'][desde_nodo][hacia_nodo]

    transit_callback_index = routing.RegisterTransitCallback(
        distancia_callback
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        transit_callback_index
    )

    def demanda_callback(desde_index):

        desde_nodo = manager.IndexToNode(desde_index)

        return datos['demandas'][desde_nodo]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demanda_callback
    )

    routing.AddDimensionWithVehicleCapacity(

        demand_callback_index,
        0,
        datos['capacidades_vehiculos'],
        True,
        'Capacidad'

    )

    parametros_busqueda = pywrapcp.DefaultRoutingSearchParameters()

    parametros_busqueda.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    parametros_busqueda.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    parametros_busqueda.time_limit.seconds = 10

    solucion = routing.SolveWithParameters(
        parametros_busqueda
    )

    return datos, solucion, manager, routing


# ============================================================
# EJECUTAR
# ============================================================

datos, solucion, manager, routing = resolver_modelo()

if solucion:

    rutas = extraer_rutas(
        datos,
        manager,
        routing,
        solucion
    )

    st.success("La flota SI es suficiente para cubrir la demanda.")

    demanda_total = sum(datos['demandas'])
    capacidad_total = sum(datos['capacidades_vehiculos'])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Demanda Total", f"{demanda_total} kg")

    with col2:
        st.metric("Capacidad Total", f"{capacidad_total} kg")

    resultados = []

    st.subheader("📦 Resultados de Vehículos")

    for r in rutas:

        vehiculo = r['vehiculo']
        ruta = r['ruta']

        carga_total = 0

        nombres_ruta = []

        for nodo in ruta:

            nombres_ruta.append(
                datos['nombres_nodos'][nodo]
            )

            carga_total += datos['demandas'][nodo]

        capacidad = datos['capacidades_vehiculos'][vehiculo - 1]

        utilizacion = (
            carga_total / capacidad
        ) * 100

        distancia_km = r['distancia'] / 1000

        resultados.append({

            "Vehículo": vehiculo,
            "Ruta": " → ".join(nombres_ruta),
            "Carga (kg)": carga_total,
            "Capacidad (kg)": capacidad,
            "Utilización (%)": round(utilizacion, 2),
            "Distancia (km)": round(distancia_km, 2)

        })

    df = pd.DataFrame(resultados)

    st.dataframe(df, use_container_width=True)

    st.subheader("📍 Gráfico de Rutas")

    fig, ax = plt.subplots(figsize=(10,8))

    colores = ['blue', 'green']

    for i, coord in enumerate(datos['coordenadas']):

        ax.scatter(
            coord[1],
            coord[0],
            s=250
        )

        ax.text(
            coord[1],
            coord[0],
            datos['nombres_nodos'][i]
        )

    for idx, ruta in enumerate(rutas):

        x = []
        y = []

        for nodo in ruta['ruta']:

            y.append(
                datos['coordenadas'][nodo][0]
            )

            x.append(
                datos['coordenadas'][nodo][1]
            )

        ax.plot(
            x,
            y,
            linewidth=2,
            color=colores[idx],
            label=f'Vehículo {ruta["vehiculo"]}'
        )

    ax.set_title("Rutas Óptimas")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

else:

    st.error("No se encontró solución válida.")
