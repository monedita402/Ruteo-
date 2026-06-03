import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(

    page_title="Logistic Intelligence System",
    layout="wide"

)

# ============================================================
# ESTILO PROFESIONAL
# ============================================================

st.markdown("""

<style>

/* Fondo principal */

.stApp {

    background-color: #0E1117;
    color: white;

}

/* Sidebar */

section[data-testid="stSidebar"] {

    background-color: #161B22;
    border-right: 2px solid #1F2937;

}

/* Títulos */

h1, h2, h3 {

    color: #4FA3FF;

}

/* Métricas */

div[data-testid="metric-container"] {

    background-color: #1E293B;
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.4);

}

/* Dataframe */

[data-testid="stDataFrame"] {

    border-radius: 10px;
    overflow: hidden;

}

/* Botones */

.stButton>button {

    background-color: #2563EB;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;

}

.stButton>button:hover {

    background-color: #1D4ED8;

}

/* Inputs */

.stNumberInput {

    background-color: #111827;
    border-radius: 10px;

}

/* Alertas */

.stAlert {

    border-radius: 12px;

}

</style>

""", unsafe_allow_html=True)

# ============================================================
# TÍTULOS
# ============================================================

st.title("🚛 Logistic Intelligence System")

st.subheader(
    "Advanced Transportation & Route Optimization"
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Simulation Configuration")

num_vehiculos = st.sidebar.number_input(

    "Number of Vehicles",
    min_value=1,
    max_value=10,
    value=2

)

capacidad_vehiculo = st.sidebar.number_input(

    "Vehicle Capacity (kg)",
    min_value=500,
    max_value=10000,
    value=4000

)

# ============================================================
# DEMANDAS
# ============================================================

st.sidebar.subheader("📦 Customer Demand")

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
# MODELO DATOS
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
# EJECUCIÓN
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

    st.success(
        "Optimization completed successfully"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(

            "Total Demand",
            f"{demanda_total} kg"

        )

    with col2:

        st.metric(

            "Total Capacity",
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

        utilizacion = (

            carga / capacidad_vehiculo

        ) * 100

        resultados.append({

            "Vehicle": r['vehiculo'],
            "Route": " → ".join(nombres),
            "Load (kg)": carga,
            "Utilization %": round(utilizacion, 2),
            "Distance (km)": round(

                r['distancia'] / 1000,
                2

            )

        })

    df = pd.DataFrame(resultados)

    st.subheader("📊 Operational Analytics")

    st.dataframe(

        df,
        use_container_width=True

    )

    # ALERTAS

    for r in resultados:

        if r["Utilization %"] >= 95:

            st.warning(

                f"Vehicle {r['Vehicle']} exceeds 95% capacity"

            )

    # ========================================================
    # GRÁFICA
    # ========================================================

    st.subheader("🗺️ Route Visualization Dashboard")

    fig, ax = plt.subplots(figsize=(10,8))

    colores = [

        'cyan',
        'lime',
        'orange',
        'magenta',
        'yellow'

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
            linewidth=3,
            color=colores[idx % len(colores)],
            label=f'Vehicle {ruta["vehiculo"]}'

        )

    ax.set_title(

        "Optimized Transportation Routes",
        color='white'

    )

    ax.set_facecolor('#0E1117')

    fig.patch.set_facecolor('#0E1117')

    ax.tick_params(colors='white')

    ax.legend()

    ax.grid(True)

    st.pyplot(fig)

else:

    st.error(

        "No feasible solution found"

    )
