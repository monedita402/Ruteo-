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
# CSS PREMIUM + FIX IDIOMA + BOTONES
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0B1120;
    color: white;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0F172A,#111827);
    border-right: 2px solid #1E293B;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #FFFFFF !important;
}

/* FIX IDIOMA VISIBILIDAD */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1E293B !important;
    color: white !important;
}

.stSelectbox span {
    color: white !important;
}

div[role="option"] {
    color: black !important;
}

/* INPUTS */
.stNumberInput input {
    background-color: #1E293B !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
}

/* BOTONES */
.stButton > button {
    background-color: #1E293B !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
    transition: 0.3s;
}

.stButton > button:hover {
    background-color: #2563EB !important;
    transform: scale(1.03);
}

/* TITULOS */
h1 {
    color: white !important;
    font-size: 48px !important;
    font-weight: 800 !important;
}

h2, h3 {
    color: #60A5FA !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# IDIOMA
# ============================================================

idioma = st.sidebar.selectbox(
    "🌎 Idioma / Language",
    ["Español", "English"]
)

st.sidebar.markdown("---")

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
# TÍTULO
# ============================================================

st.title(TITULO)
st.subheader(SUBTITULO)

# ============================================================
# SIDEBAR CONFIG
# ============================================================

st.sidebar.header(CONFIG)

num_vehiculos = st.sidebar.number_input(VEHICULOS, 1, 10, 2)
capacidad = st.sidebar.number_input(CAPACIDAD, 500, 10000, 4000)

st.sidebar.subheader(DEMANDAS)

demanda_poblado = st.sidebar.number_input("El Poblado", value=1800)
demanda_envigado = st.sidebar.number_input("Envigado", value=1200)
demanda_itagui = st.sidebar.number_input("Itagüí", value=1500)
demanda_bello = st.sidebar.number_input("Bello", value=2200)
demanda_laureles = st.sidebar.number_input("Laureles", value=900)

# ============================================================
# CLIENTES DINÁMICOS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.subheader("📦 Gestión de Clientes")

if "clientes" not in st.session_state:
    st.session_state.clientes = []

cli_nombre = st.sidebar.text_input("Nombre Cliente")
cli_demanda = st.sidebar.number_input("Demanda Cliente", value=100)
cli_lat = st.sidebar.number_input("Lat Cliente", value=6.200, format="%.3f", step=0.001)
cli_lon = st.sidebar.number_input("Lon Cliente", value=-75.600, format="%.3f", step=0.001)

if st.sidebar.button("➕ Agregar Cliente"):
    if cli_nombre != "":
        st.session_state.clientes.append({
            "nombre": cli_nombre,
            "demanda": cli_demanda,
            "coord": [cli_lat, cli_lon]
        })

if len(st.session_state.clientes) > 0:

    st.sidebar.markdown("---")
    st.sidebar.subheader("🗑️ Eliminar Cliente")

    cliente_borrar = st.sidebar.selectbox(
        "Selecciona cliente",
        [c["nombre"] for c in st.session_state.clientes]
    )

    if st.sidebar.button("❌ Eliminar Cliente"):
        st.session_state.clientes = [
            c for c in st.session_state.clientes
            if c["nombre"] != cliente_borrar
        ]
        st.rerun()

# ============================================================
# DATOS BASE
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
# CLIENTES DINÁMICOS AL MODELO
# ============================================================

for c in st.session_state.clientes:
    coordenadas.append(c["coord"])
    nombres.append(c["nombre"])
    demandas.append(c["demanda"])

# ============================================================
# TABLA CLIENTES (FIJOS + DINÁMICOS)
# ============================================================

clientes_fijos = [
    {"nombre": "El Poblado", "demanda": demanda_poblado},
    {"nombre": "Envigado", "demanda": demanda_envigado},
    {"nombre": "Itagüí", "demanda": demanda_itagui},
    {"nombre": "Bello", "demanda": demanda_bello},
    {"nombre": "Laureles", "demanda": demanda_laureles},
]

tabla = []

for c in clientes_fijos:
    tabla.append({"Tipo": "Fijo", "Nombre": c["nombre"], "Demanda": c["demanda"]})

for c in st.session_state.clientes:
    tabla.append({"Tipo": "Dinámico", "Nombre": c["nombre"], "Demanda": c["demanda"]})

st.subheader("📋 Clientes (Fijos + Dinámicos)")
st.dataframe(pd.DataFrame(tabla), use_container_width=True)

# ============================================================
# DISTANCIA
# ============================================================

def calcular_distancia(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    return int(math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111000)

matriz = [
    [
        calcular_distancia(coordenadas[i], coordenadas[j])
        for j in range(len(coordenadas))
    ]
    for i in range(len(coordenadas))
]

# ============================================================
# MODELO OR-TOOLS
# ============================================================

manager = pywrapcp.RoutingIndexManager(
    len(matriz),
    num_vehiculos,
    0
)

routing = pywrapcp.RoutingModel(manager)

def callback_distancia(i, j):
    return matriz[
        manager.IndexToNode(i)
    ][
        manager.IndexToNode(j)
    ]

routing.SetArcCostEvaluatorOfAllVehicles(
    routing.RegisterTransitCallback(callback_distancia)
)

def callback_demanda(i):
    return demandas[manager.IndexToNode(i)]

routing.AddDimensionWithVehicleCapacity(
    routing.RegisterUnaryTransitCallback(callback_demanda),
    0,
    [capacidad] * num_vehiculos,
    True,
    "Capacity"
)

params = pywrapcp.DefaultRoutingSearchParameters()
params.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

solucion = routing.SolveWithParameters(params)

# ============================================================
# RESULTADOS
# ============================================================

if solucion:

    st.success(EXITO)

    resultados = []

    fig, ax = plt.subplots(figsize=(10, 8))

    colores = ['cyan', 'lime', 'orange', 'magenta', 'yellow']

    for i, coord in enumerate(coordenadas):
        ax.scatter(coord[1], coord[0], s=250, color='white')
        ax.text(coord[1], coord[0], nombres[i], color='white')

    for vehiculo in range(num_vehiculos):

        index = routing.Start(vehiculo)
        ruta = []
        carga = 0
        distancia_total = 0

        while not routing.IsEnd(index):

            nodo = manager.IndexToNode(index)
            ruta.append(nombres[nodo])
            carga += demandas[nodo]

            prev = index
            index = solucion.Value(routing.NextVar(index))

            distancia_total += routing.GetArcCostForVehicle(
                prev, index, vehiculo
            )

        ruta.append("CEDI Sabaneta")

        resultados.append({
            "Vehículo": vehiculo + 1,
            "Ruta": " → ".join(ruta),
            "Carga (kg)": carga,
            "Utilización %": round((carga / capacidad) * 100, 2),
            "Distancia (km)": round(distancia_total / 1000, 2)
        })

        x, y = [], []

        for p in ruta[:-1]:
            idx = nombres.index(p)
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

    st.subheader(RESULTADOS)
    st.dataframe(pd.DataFrame(resultados), use_container_width=True)

    st.subheader(MAPA)
    ax.set_facecolor('#0B1120')
    fig.patch.set_facecolor('#0B1120')
    ax.tick_params(colors='white')
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)

else:
    st.error(ERROR)
