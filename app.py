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
# ESTILO PROFESIONAL PREMIUM
# ============================================================

st.markdown("""

<style>

/* Fondo principal */

.stApp {

    background-color: #0B1120;
    color: white;

}

/* Sidebar */

section[data-testid="stSidebar"] {

    background-color: #111827;
    border-right: 2px solid #1E293B;

}

/* Texto sidebar */

section[data-testid="stSidebar"] * {

    color: #F9FAFB !important;

}

/* Títulos */

h1 {

    color: white !important;
    font-size: 48px !important;
    font-weight: 800 !important;

}

h2, h3 {

    color: #60A5FA !important;
    font-weight: 700 !important;

}

/* Texto general */

p, label, div {

    color: #E5E7EB;

}

/* KPIs */

div[data-testid="metric-container"] {

    background: linear-gradient(
        135deg,
        #1E293B,
        #0F172A
    );

    border: 1px solid #334155;

    padding: 25px;

    border-radius: 18px;

    box-shadow: 0px 6px 18px rgba(0,0,0,0.45);

}

/* Texto KPIs */

div[data-testid="metric-container"] label {

    color: #94A3B8 !important;
    font-size: 15px !important;

}

div[data-testid="metric-container"] div {

    color: white !important;
    font-size: 30px !important;
    font-weight: bold !important;

}

/* Tabla */

[data-testid="stDataFrame"] {

    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #334155;

}

/* Botones */

.stButton>button {

    background: linear-gradient(
        135deg,
        #2563EB,
        #1D4ED8
    );

    color: white;

    border-radius: 12px;

    border: none;

    padding: 12px 20px;

    font-weight: bold;

}

/* Inputs */

.stNumberInput input {

    background-color: #1E293B !important;
    color: white !important;
    border-radius: 10px !important;

}

/* Alertas */

.stAlert {

    border-radius: 14px;

}

</style>

""", unsafe_allow_html=True)

# ============================================================
# SELECTOR DE IDIOMA
# ============================================================

idioma = st.sidebar.selectbox(

    "🌎 Idioma / Language",

    [

        "Español",
        "English"

    ]

)

# ============================================================
# TEXTOS DINÁMICOS
# ============================================================

if idioma == "Español":

    TITULO = "🚛 Sistema Inteligente de Logística"

    SUBTITULO = "Optimización Avanzada de Transporte y Rutas"

    CONFIG = "⚙️ Configuración de Simulación"

    VEHICULOS = "Cantidad de Vehículos"

    CAPACIDAD = "Capacidad del Vehículo (kg)"

    DEMANDAS = "📦 Demanda de Clientes"

    DEMANDA_TOTAL = "Demanda Total"

    CAPACIDAD_TOTAL = "Capacidad Total"

    RESULTADOS = "📊 Analítica Operacional"

    MAPA = "🗺️ Visualización de Rutas"

    EXITO = "Optimización realizada correctamente"

    ERROR = "No existe solución válida"

    ALERTA = "supera el 95% de capacidad"

else:

    TITULO = "🚛 Logistic Intelligence System"

    SUBTITULO = "Advanced Transportation & Route Optimization"

    CONFIG = "⚙️ Simulation Configuration"

    VEHICULOS = "Number of Vehicles"

    CAPACIDAD = "Vehicle Capacity (kg)"

    DEMANDAS = "📦 Customer Demand"

    DEMANDA_TOTAL = "Total Demand"

    CAPACIDAD_TOTAL = "Total Capacity"

    RESULTADOS = "📊 Operational Analytics"

    MAPA = "🗺️ Route Visualization Dashboard"

    EXITO = "Optimization completed successfully"

    ERROR = "No feasible solution found"

    ALERTA = "exceeds 95% capacity"

# ============================================================
# TÍTULOS
# ============================================================

st.title(TITULO)

st.subheader(SUBTITULO)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(CONFIG)

num_vehiculos = st.sidebar.number_input(

    VEHICULOS,
    min_value=1,
    max_value=10,
    value=2

)

capacidad_vehiculo = st.sidebar.number_input(

    CAPACIDAD,
    min_value=500,
    max_value=10000,
    value=4000

)

# ============================================================
# DEMANDAS
# ============================================================

st.sidebar.subheader(DEMANDAS)

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
# FUNCIÓN DISTANCIA
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
# CREACIÓN DE DATOS
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

    st.success(EXITO)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(

            DEMANDA_TOTAL,
            f"{demanda_total} kg"

        )

    with col2:

        st.metric(

            CAPACIDAD_TOTAL,
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

            "Vehículo": r['vehiculo'],
            "Ruta": " → ".join(nombres),
            "Carga (kg)": carga,
            "Utilización %": round(utilizacion, 2),
            "Distancia (km)": round(

                r['distancia'] / 1000,
                2

            )

        })

    df = pd.DataFrame(resultados)

    st.subheader(RESULTADOS)

    st.dataframe(

        df,
        use_container_width=True

    )

    for r in resultados:

        if r["Utilización %"] >= 95:

            st.warning(

                f"Vehículo {r['Vehículo']} {ALERTA}"

            )

    # ========================================================
    # GRÁFICA
    # ========================================================

    st.subheader(MAPA)

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
            s=250,
            color='white'

        )

        ax.text(

            coord[1],
            coord[0],
            datos['nombres'][i],
            color='white'

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
            label=f'Vehículo {ruta["vehiculo"]}'

        )

    ax.set_title(

        "Optimized Transportation Routes",
        color='white'

    )

    ax.set_facecolor('#0B1120')

    fig.patch.set_facecolor('#0B1120')

    ax.tick_params(colors='white')

    ax.legend()

    ax.grid(True)

    st.pyplot(fig)

else:

    st.error(ERROR)
