import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Optimización Logística",
    layout="wide"
)

st.title("🚚 Sistema de Optimización Logística")
st.subheader("Distribución Inteligente de Rutas - Expreso de la Montaña")

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Configuración de Simulación")

num_vehiculos = st.sidebar.number_input(
    "Cantidad de Vehículos",
    min_value=1,
    max_value=10,
    value=2
)

capacidad_vehiculo = st.sidebar.number_input(
    "Capacidad por Vehículo (kg)",
    min_value=500,
    max_value=10000,
    value=4000
)

# ============================================================
# DATOS CLIENTES
# ============================================================

st.sidebar.subheader("Demandas de Clientes")

demanda_poblado = st.sidebar.number_input(
    "El Poblado",
    value=1800
)

demanda_envigado = st.sidebar.number_input(
    "Envigado",
    value=1200
)

demanda_itagui = st.sidebar.number_input(
    "Itagüí",
    value=1500
)

demanda_bello = st.sidebar.number_input(
    "Bello",
    value=2200
)

demanda_laureles = st.sidebar.number_input(
    "Laureles",
    value=900
)

# ============================================================
# DISTANCIA
# ============================================================

def calcular_distancia(coord1, coord2):

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    distancia = math.sqrt(
        delta_lat**2 + delta_lon**2
    )

    return int(distancia * 111000)

# ============================================================
# MODELO
# ============================================================

def crear_datos():

    datos = {}

    datos['coordenadas'] = [

        [6.151, -75.615],
        [6.210, -75.571],
        [6.173, -75.583],
        [6.172, -75.609],
        [6.333, -75.558],
        [6.243, -75.594]

    ]

    datos['nombres'] = [

        "CEDI Sabaneta",
        "El Poblado",
        "Envigado",
        "Itagüí",
        "Bello",
        "Laureles"

    ]

    datos['demandas'] = [

        0,
        demanda_poblado,
        demanda_envigado,
        demanda_itagui,
        demanda_bello,
        demanda_laureles

    ]

    datos['num_vehiculos'] = num_vehiculos

    datos['capacidades'] = [
        capacidad_vehiculo
    ] * num_vehiculos

    datos['deposito'] = 0

    # MATRIZ DISTANCIAS

    matriz = []

    for i in range(len(datos['coordenadas'])):

        fila = []

        for j in range(len(datos['coordenadas'])):

            distancia = calcular_distancia(
                datos['coordenadas'][i],
                datos['coordenadas'][j]
            )

            fila.append(distancia)

        matriz.append(fila)

    datos['matriz'] = matriz

    return datos

# ============================================================
# RESOLVER MODELO
# ============================================================

def resolver():

    datos = crear_datos()

    manager = pywrapcp.RoutingIndexManager(

        len(datos['matriz']),
        datos['num_vehiculos'],
        datos['deposito']

    )

    routing = pywrapcp.RoutingModel(manager)

    # DISTANCIA

    def distancia_callback(desde, hacia):

        desde_nodo = manager.IndexToNode(desde)
        hacia_nodo = manager.IndexToNode(hacia)

        return datos['matriz'][desde_nodo][hacia_nodo]

    transit_callback = routing.RegisterTransitCallback(
        distancia_callback
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        transit_callback
    )

    # DEMANDA

    def demanda_callback(desde):

        desde_nodo = manager.IndexToNode(desde)

        return datos['demandas'][desde_nodo]

    demand_callback = routing.RegisterUnaryTransitCallback(
        demanda_callback
    )

    routing.AddDimensionWithVehicleCapacity(

        demand_callback,
        0,
        datos['capacidades'],
        True,
        'Capacidad'

    )

    # BÚSQUEDA

    parametros = pywrapcp.DefaultRoutingSearchParameters()

    parametros.first_solution_strategy = (

        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    parametros.local_search_metaheuristic = (

        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    parametros.time_limit.seconds = 10

    solucion = routing.SolveWithParameters(parametros)

    return datos, solucion, manager, routing

# ============================================================
# EXTRAER RUTAS
# ============================================================

def obtener_rutas(datos, manager, routing, solucion):

    rutas = []

    for vehiculo in range(datos['num_vehiculos']):

        index = routing.Start(vehiculo)

        ruta = []

        distancia_total = 0

        while not routing.IsEnd(index):

            nodo = manager.IndexToNode(index)

            ruta.append(nodo)

            previo = index

            index = solucion.Value(
                routing.NextVar(index)
            )

            distancia_total += routing.GetArcCostForVehicle(
                previo,
                index,
                vehiculo
            )

        ruta.append(manager.IndexToNode(index))

        rutas.append({

            "vehiculo": vehiculo + 1,
            "ruta": ruta,
            "distancia": distancia_total

        })

    return rutas

# ============================================================
# EJECUTAR
# ============================================================

datos, solucion, manager, routing = resolver()

if solucion:

    rutas = obtener_rutas(
        datos,
        manager,
        routing,
        solucion
    )

    demanda_total = sum(datos['demandas'])

    capacidad_total = sum(datos['capacidades'])

    st.success("Optimización realizada correctamente")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Demanda Total",
            f"{demanda_total} kg"
        )

    with col2:

        st.metric(
            "Capacidad Total",
            f"{capacidad_total} kg"
        )

    resultados = []

    for r in rutas:

        carga = 0

        nombres = []

        for nodo in r['ruta']:

            nombres.append(
                datos['nombres'][nodo]
            )

            carga += datos['demandas'][nodo]

        capacidad = capacidad_vehiculo

        utilizacion = (
            carga / capacidad
        ) * 100

        resultados.append({

            "Vehículo": r['vehiculo'],
            "Ruta": " → ".join(nombres),
            "Carga": carga,
            "Utilización %": round(utilizacion, 2),
            "Distancia km": round(
                r['distancia'] / 1000,
                2
            )

        })

    df = pd.DataFrame(resultados)

    st.subheader("Resultados Logísticos")

    st.dataframe(
        df,
        use_container_width=True
    )

    # ALERTAS

    for r in resultados:

        if r["Utilización %"] >= 95:

            st.warning(
                f"Vehículo {r['Vehículo']} supera el 95% de capacidad"
            )

    # ========================================================
    # GRÁFICO
    # ========================================================

    st.subheader("Mapa de Rutas")

    fig, ax = plt.subplots(figsize=(10,8))

    colores = [

        'blue',
        'green',
        'red',
        'orange',
        'purple'

    ]

    for i, coord in enumerate(datos['coordenadas']):

        ax.scatter(
            coord[1],
            coord[0],
            s=250
        )

        ax.text(
            coord[1],
            coord[0],
            datos['nombres'][i]
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
            color=colores[idx % len(colores)],
            label=f'Vehículo {ruta["vehiculo"]}'
        )

    ax.set_title("Rutas Optimizadas")
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)

else:

    st.error(
        "No existe solución con la capacidad configurada"
    )
