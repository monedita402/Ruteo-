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
# CSS PREMIUM (CON CONTRASTE ARREGLADO)
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0B1120;
    color: white;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0F172A,#111827);
    border-right: 2px solid #1E293B;
}

/* MEJOR CONTRASTE SELECTBOX */
.stSelectbox label {
    color: #60A5FA !important;
    font-weight: 700;
}

/* INPUTS */
.stNumberInput input {
    background-color: #1E293B !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
}

/* TÍTULOS */
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
# IDIOMA (ARREGLADO VISUAL)
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
# DATOS FIJOS
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
# ELIMINAR CLIENTE (ARREGLADO Y FUNCIONAL)
# ============================================================

# Nota: aquí no hay clientes dinámicos en este modelo
# pero se deja estructura limpia si luego quieres extenderlo

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

    # NODOS CON NOMBRES VISIBLES
    for i, coord in enumerate(coordenadas):
        ax.scatter(coord[1], coord[0], s=250, color='white')
        ax.text(coord[1], coord[0], nombres[i], color='white')

    # RUTAS
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
                prev,
                index,
                vehiculo
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

# ============================================================
# FOOTER AUTORES (ARREGLADO Y FINAL)
# ============================================================

st.markdown("""
<hr style="border:1px solid #334155; margin-top:40px;">

<div style='text-align:center; padding:25px;'>

<h2 style="color:#60A5FA;">👨‍💻 Autores del Proyecto</h2>

<p style="color:white; font-size:20px;">
Miguel Ángel Monedero Aguado
</p>

<p style="color:#CBD5E1;">
📞 31843741842
</p>

<br>

<p style="color:white; font-size:20px;">
Cristhyan Felipe Uran España
</p>

<p style="color:#CBD5E1;">
📞 3105482523
</p>

<br>

<p style="color:#94A3B8; font-size:14px;">
Sistema Inteligente de Logística • Streamlit • OR-Tools
</p>

</div>
""", unsafe_allow_html=True)
