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
    page_title="Sistema Logístico Configurable",
    layout="wide"
)

st.title("🚛 Sistema Inteligente de Logística Configurable")

# ============================================================
# SESSION STATE
# ============================================================

if "cedis" not in st.session_state:
    st.session_state.cedis = [
        {"nombre": "CEDI Sabaneta", "coord": [6.151, -75.615]}
    ]

if "clientes" not in st.session_state:
    st.session_state.clientes = []

# ============================================================
# SIDEBAR CONFIGURACIÓN
# ============================================================

st.sidebar.header("⚙️ Configuración")

num_vehiculos = st.sidebar.number_input("Vehículos", 1, 10, 2)
capacidad = st.sidebar.number_input("Capacidad vehículo", 500, 10000, 4000)

# ============================================================
# CEDIS DINÁMICOS
# ============================================================

st.sidebar.subheader("🏢 Agregar CEDI")

cedi_nombre = st.sidebar.text_input("Nombre CEDI")
cedi_lat = st.sidebar.number_input("Lat CEDI", value=6.15)
cedi_lon = st.sidebar.number_input("Lon CEDI", value=-75.61)

if st.sidebar.button("➕ Agregar CEDI"):
    st.session_state.cedis.append({
        "nombre": cedi_nombre,
        "coord": [cedi_lat, cedi_lon]
    })

# ============================================================
# CLIENTES DINÁMICOS
# ============================================================

st.sidebar.subheader("📦 Agregar Cliente")

cli_nombre = st.sidebar.text_input("Nombre Cliente")
cli_demanda = st.sidebar.number_input("Demanda", value=100)
cli_lat = st.sidebar.number_input("Lat Cliente", value=6.20)
cli_lon = st.sidebar.number_input("Lon Cliente", value=-75.60)

if st.sidebar.button("➕ Agregar Cliente"):
    st.session_state.clientes.append({
        "nombre": cli_nombre,
        "demanda": cli_demanda,
        "coord": [cli_lat, cli_lon]
    })

# ============================================================
# MOSTRAR DATOS
# ============================================================

st.subheader("🏢 CEDIs")
st.write(st.session_state.cedis)

st.subheader("📦 Clientes")
st.write(st.session_state.clientes)

# ============================================================
# VALIDACIÓN
# ============================================================

if len(st.session_state.clientes) == 0:
    st.warning("Agrega al menos un cliente para optimizar rutas")
    st.stop()

# ============================================================
# SELECCIÓN CEDI BASE
# ============================================================

cedi_base = st.sidebar.selectbox(
    "CEDI base",
    [c["nombre"] for c in st.session_state.cedis]
)

# ============================================================
# CONSTRUIR MODELO
# ============================================================

coordenadas = []
nombres = []
demandas = []

# CEDIs
for c in st.session_state.cedis:
    coordenadas.append(c["coord"])
    nombres.append(c["nombre"])
    demandas.append(0)

# Clientes
for c in st.session_state.clientes:
    coordenadas.append(c["coord"])
    nombres.append(c["nombre"])
    demandas.append(c["demanda"])

depot_index = nombres.index(cedi_base)

# ============================================================
# DISTANCIA
# ============================================================

def distancia(a, b):
    return int(math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) * 111000)

# matriz
matriz = [
    [distancia(i, j) for j in coordenadas]
    for i in coordenadas
]

# ============================================================
# MODELO OR-TOOLS
# ============================================================

manager = pywrapcp.RoutingIndexManager(
    len(matriz),
    num_vehiculos,
    depot_index
)

routing = pywrapcp.RoutingModel(manager)

def callback(i, j):
    return matriz[
        manager.IndexToNode(i)
    ][
        manager.IndexToNode(j)
    ]

transit = routing.RegisterTransitCallback(callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit)

def demand(i):
    return demandas[manager.IndexToNode(i)]

demand_callback = routing.RegisterUnaryTransitCallback(demand)

routing.AddDimensionWithVehicleCapacity(
    demand_callback,
    0,
    [capacidad] * num_vehiculos,
    True,
    "Capacity"
)

params = pywrapcp.DefaultRoutingSearchParameters()
params.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

solution = routing.SolveWithParameters(params)

# ============================================================
# RESULTADOS
# ============================================================

if solution:

    st.success("Optimización exitosa 🚀")

    resultados = []

    fig, ax = plt.subplots(figsize=(10, 7))

    colors = ["cyan", "lime", "orange", "magenta", "yellow"]

    # nodos
    for i, c in enumerate(coordenadas):
        ax.scatter(c[1], c[0], s=200, color="white")
        ax.text(c[1], c[0], nombres[i], color="white")

    for v in range(num_vehiculos):

        index = routing.Start(v)
        ruta = []
        carga = 0
        distancia_total = 0

        while not routing.IsEnd(index):

            node = manager.IndexToNode(index)
            ruta.append(nombres[node])
            carga += demandas[node]

            prev = index
            index = solution.Value(routing.NextVar(index))

            distancia_total += routing.GetArcCostForVehicle(
                prev, index, v
            )

        ruta.append(cedi_base)

        resultados.append({
            "Vehículo": v + 1,
            "Ruta": " → ".join(ruta),
            "Carga": carga,
            "Utilización %": round((carga / capacidad) * 100, 2),
            "Distancia km": round(distancia_total / 1000, 2)
        })

        x, y = [], []

        for p in ruta[:-1]:
            idx = nombres.index(p)
            x.append(coordenadas[idx][1])
            y.append(coordenadas[idx][0])

        x.append(coordenadas[depot_index][1])
        y.append(coordenadas[depot_index][0])

        ax.plot(
            x, y,
            linewidth=3,
            color=colors[v % len(colors)],
            label=f"Vehículo {v+1}"
        )

    st.subheader("📊 Resultados")
    st.dataframe(pd.DataFrame(resultados), use_container_width=True)

    st.subheader("🗺️ Rutas")
    ax.set_facecolor("#0B1120")
    fig.patch.set_facecolor("#0B1120")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

else:
    st.error("No se encontró solución")
