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

    page_title="Sistema Inteligente de Logística",
    layout="wide"

)

# ============================================================
# CSS PREMIUM
# ============================================================

st.markdown("""

<style>

/* Fondo */

.stApp {

    background-color: #0B1120;
    color: white;

}

/* Sidebar */

section[data-testid="stSidebar"] {

    background: linear-gradient(
        180deg,
        #0F172A,
        #111827
    );

    border-right: 2px solid #1E293B;

}

/* Textos sidebar */

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {

    color: white !important;

}

/* Selectbox */

.stSelectbox div[data-baseweb="select"] {

    background-color: #1E293B !important;

    border-radius: 12px !important;

    border: 1px solid #334155 !important;

}

.stSelectbox div[data-baseweb="select"] span {

    color: white !important;

}

div[role="listbox"] {

    background-color: #1E293B !important;

}

div[role="option"] {

    color: white !important;

}

div[role="option"]:hover {

    background-color: #2563EB !important;

}

/* Inputs */

.stNumberInput input {

    background-color: #1E293B !important;

    color: white !important;

    border-radius: 10px !important;

}

/* Títulos */

h1 {

    color: white !important;

    font-size: 48px !important;

    font-weight: 800 !important;

}

h2, h3 {

    color: #60A5FA !important;

}

/* KPIs */

div[data-testid="metric-container"] {

    background: linear-gradient(
        135deg,
        #1E293B,
        #0F172A
    );

    border: 2px solid #475569;

    padding: 28px;

    border-radius: 20px;

    box-shadow:
        0px 6px 18px rgba(0,0,0,0.45),
        0px 0px 12px rgba(96,165,250,0.15);

}

/* KPI Texto */

div[data-testid="metric-container"] label {

    color: white !important;

    font-size: 20px !important;

    font-weight: 800 !important;

}

/* KPI Valor */

div[data-testid="metric-container"] div {

    color: #F8FAFC !important;

    font-size: 42px !important;

    font-weight: 900 !important;

}

/* Tabla */

[data-testid="stDataFrame"] {

    border-radius: 14px;

    overflow: hidden;

}

/* Alertas */

.stAlert {

    border-radius: 14px;

}

</style>

""", unsafe_allow_html=True)

# ============================================================
# IDIOMA
# ============================================================

idioma = st.sidebar.selectbox(

    "🌎 Idioma / Language",

    [

        "Español",
        "English"

    ]

)

# ============================================================
# TEXTOS
# ============================================================

if idioma == "Español":

    TITULO = "🚛 Sistema Inteligente de Logística"

    SUBTITULO = "Optimización Avanzada de Transporte y Rutas"

    CONFIG = "⚙️ Configuración"

    VEHICULOS = "Cantidad de Vehículos"

    CAPACIDAD = "Capacidad Vehículo (kg)"

    DEMANDAS = "📦 Demandas"

    RESULTADOS = "📊 Resultados"

    MAPA = "🗺️ Visualización de Rutas"

    EXITO = "Optimización realizada correctamente"

    ERROR = "No existe solución válida"

else:

    TITULO = "🚛 Logistic Intelligence System"

    SUBTITULO = "Advanced Transportation & Route Optimization"

    CONFIG = "⚙️ Configuration"

    VEHICULOS = "Number of Vehicles"

    CAPACIDAD = "Vehicle Capacity"

    DEMANDAS = "📦 Demands"

    RESULTADOS = "📊 Results"

    MAPA = "🗺️ Route Visualization"

    EXITO = "Optimization completed successfully"

    ERROR = "No feasible solution"

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

capacidad = st.sidebar.number_input(

    CAPACIDAD,
    min_value=500,
    max_value=10000,
    value=4000

)

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
# DATOS
# ============================================================

coordenadas = [

    [6.151, -75.615],
    [6.210, -75.571],
    [6.173, -75.583],
    [6.172, -75.609],
    [6.333, -75.558],
    [6.243, -75.594]

]

nombres = [

    "CEDI Sabaneta",
    "El Poblado",
    "Envigado",
    "Itagüí",
    "Bello",
    "Laureles"

]

demandas = [

    0,
    demanda_poblado,
    demanda_envigado,
    demanda_itagui,
    demanda_bello,
    demanda_laureles

]

# ============================================================
# DISTANCIA
# ============================================================

def calcular_distancia(coord1, coord2):

    lat1, lon1 = coord1

    lat2, lon2 = coord2

    return int(

        math.sqrt(

            (lat2 - lat1)**2 +
            (lon2 - lon1)**2

        ) * 111000

    )

# ============================================================
# MATRIZ
# ============================================================

matriz = []

for i in range(len(coordenadas)):

    fila = []

    for j in range(len(coordenadas)):

        fila.append(

            calcular_distancia(

                coordenadas[i],
                coordenadas[j]

            )

        )

    matriz.append(fila)

# ============================================================
# MODELO
# ============================================================

manager = pywrapcp.RoutingIndexManager(

    len(matriz),
    num_vehiculos,
    0

)

routing = pywrapcp.RoutingModel(manager)

def callback_distancia(desde, hacia):

    return matriz[
        manager.IndexToNode(desde)
    ][
        manager.IndexToNode(hacia)
    ]

transit_callback = routing.RegisterTransitCallback(

    callback_distancia

)

routing.SetArcCostEvaluatorOfAllVehicles(

    transit_callback

)

def callback_demanda(desde):

    return demandas[
        manager.IndexToNode(desde)
    ]

demand_callback = routing.RegisterUnaryTransitCallback(

    callback_demanda

)

routing.AddDimensionWithVehicleCapacity(

    demand_callback,
    0,
    [capacidad] * num_vehiculos,
    True,
    'Capacity'

)

parametros = pywrapcp.DefaultRoutingSearchParameters()

parametros.first_solution_strategy = (

    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

)

solucion = routing.SolveWithParameters(parametros)

# ============================================================
# RESULTADOS
# ============================================================

if solucion:

    st.success(EXITO)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(

            "Total Demand",
            f"{sum(demandas)} kg"

        )

    with col2:

        st.metric(

            "Total Capacity",
            f"{capacidad * num_vehiculos} kg"

        )

    resultados = []

    fig, ax = plt.subplots(figsize=(10,8))

    colores = [

        'cyan',
        'lime',
        'orange',
        'magenta',
        'yellow'

    ]

    for i, coord in enumerate(coordenadas):

        ax.scatter(

            coord[1],
            coord[0],
            s=250,
            color='white'

        )

        ax.text(

            coord[1],
            coord[0],
            nombres[i],
            color='white'

        )

    for vehiculo in range(num_vehiculos):

        index = routing.Start(vehiculo)

        ruta = []

        carga = 0

        distancia_total = 0

        while not routing.IsEnd(index):

            nodo = manager.IndexToNode(index)

            ruta.append(nombres[nodo])

            carga += demandas[nodo]

            previo = index

            index = solucion.Value(

                routing.NextVar(index)

            )

            distancia_total += routing.GetArcCostForVehicle(

                previo,
                index,
                vehiculo

            )

        ruta.append("CEDI Sabaneta")

        utilizacion = (

            carga / capacidad

        ) * 100

        resultados.append({

            "Vehículo": vehiculo + 1,
            "Ruta": " → ".join(ruta),
            "Carga (kg)": carga,
            "Utilización %": round(utilizacion,2),
            "Distancia (km)": round(distancia_total / 1000,2)

        })

        x = []
        y = []

        for punto in ruta[:-1]:

            idx = nombres.index(punto)

            y.append(coordenadas[idx][0])

            x.append(coordenadas[idx][1])

        x.append(coordenadas[0][1])
        y.append(coordenadas[0][0])

        ax.plot(

            x,
            y,
            linewidth=3,
            color=colores[vehiculo % len(colores)],
            label=f'Vehículo {vehiculo+1}'

        )

    df = pd.DataFrame(resultados)

    st.subheader(RESULTADOS)

    st.dataframe(

        df,
        use_container_width=True

    )

    st.subheader(MAPA)

    ax.set_facecolor('#0B1120')

    fig.patch.set_facecolor('#0B1120')

    ax.tick_params(colors='white')

    ax.legend()

    ax.grid(True)

    st.pyplot(fig)

    # ============================================================
    # FOOTER
    # ============================================================

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("""

    <hr style="
        border:1px solid #334155;
        margin-top:40px;
        margin-bottom:30px;
    ">

    <div style="

        text-align:center;

        padding:30px;

        border-radius:20px;

        background: linear-gradient(
            135deg,
            #111827,
            #0F172A
        );

        border:1px solid #334155;

    ">

    <h2 style="
        color:#60A5FA;
        margin-bottom:25px;
        font-size:30px;
    ">

    👨‍💻 Autores del Proyecto

    </h2>

    <p style="
        color:white;
        font-size:22px;
        font-weight:bold;
    ">

    Miguel Ángel Monedero Aguado

    </p>

    <p style="
        color:#CBD5E1;
        font-size:18px;
    ">

    📞 31843741842

    </p>

    <br>

    <p style="
        color:white;
        font-size:22px;
        font-weight:bold;
    ">

    Cristhyan Felipe Uran España

    </p>

    <p style="
        color:#CBD5E1;
        font-size:18px;
    ">

    📞 3105482523

    </p>

    <br>

    <p style="
        color:#94A3B8;
        font-size:15px;
    ">

    Sistema Inteligente de Logística •
    Optimización de Rutas •
    Python • Streamlit • OR-Tools

    </p>

    </div>

    """, unsafe_allow_html=True)

else:

    st.error(ERROR)
