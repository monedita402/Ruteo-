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
    page_title="Sistema Logístico - Clientes",
    layout="wide"
)

st.title("🚛 Sistema Inteligente de Logística (CEDI Sabaneta)")

# ============================================================
# CEDI FIJO
# ============================================================

cedi = {
    "nombre": "CEDI Sabaneta",
    "coord": [6.151, -75.615]
}

# ============================================================
# SESSION STATE
# ============================================================

if "clientes" not in st.session_state:
    st.session_state.clientes = []

# ============================================================
# SIDEBAR CONFIG
# ============================================================

st.sidebar.header("⚙️ Configuración")

num_vehiculos = st.sidebar.number_input("Vehículos", 1, 10, 2)
capacidad = st.sidebar.number_input("Capacidad vehículo", 500, 10000, 4000)

# ============================================================
# AGREGAR CLIENTES
# ============================================================

st.sidebar.subheader("📦 Agregar Cliente")

cli_nombre = st.sidebar.text_input("Nombre Cliente")
cli_demanda = st.sidebar.number_input("Demanda", value=100)
cli_lat = st.sidebar.number_input("Lat Cliente", value=6.20)
cli_lon = st.sidebar.number_input("Lon Cliente", value=-75.60)

if st.sidebar.button("➕ Agregar Cliente"):
    if cli_nombre != "":
        st.session_state.clientes.append({
            "nombre": cli_nombre,
            "demanda": cli_demanda,
            "coord": [cli_lat, cli_lon]
        })

# ============================================================
# ELIMINAR CLIENTE
# ============================================================

st.sidebar.subheader("🗑️ Eliminar Cliente")

if len(st.session_state.clientes) > 0:

    cliente_a_borrar = st.sidebar.selectbox(
        "Selecciona cliente",
        [c["nombre"] for c in st.session_state.clientes]
    )

    if st.sidebar.button("❌ Eliminar cliente"):
        st.session_state.clientes = [
            c for c in st.session_state.clientes
            if c["nombre"] != cliente_a_borrar
        ]
        st.rerun()

# ============================================================
# TABLA CLIENTES
# ============================================================

st.subheader("📦 Clientes")

if len(st.session_state.clientes) > 0:

    clientes_df = pd.DataFrame(st.session_state.clientes)
    clientes_df["Lat"] = clientes_df["coord"].apply(lambda x: x[0])
    clientes_df["Lon"] = clientes_df["coord"].apply(lambda x: x[1])
    clientes_df = clientes_df.drop(columns=["coord"])

    st.dataframe(clientes_df, use_container_width=True)

# ============================================================
# VALIDACIÓN
# ============================================================

if len(st.session_state.clientes) == 0:
    st.warning("⚠️ Agrega al menos un cliente")
    st.stop()

# ============================================================
# MODELO
# ============================================================

coordenadas = [cedi["coord"]]
nombres = [cedi["nombre"]]
demandas = [0]

for c in st.session_state.clientes:
    coordenadas.append(c["coord"])
    nombres.append(c["nombre"])
    demandas.append(c["demanda"])

depot_index = 0

# ============================================================
# DISTANCIA
# ============================================================

def distancia(a, b):
    return int(math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) * 111000)

matriz = [
    [distancia(i, j) for j in coordenadas]
    for i in coordenadas
]

# ============================================================
# OR-TOOLS
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

routing.SetArcCostEvaluatorOfAllVehicles(
    routing.RegisterTransitCallback(callback)
)

def demand(i):
    return demandas[manager.IndexToNode(i)]

routing.AddDimensionWithVehicleCapacity(
    routing.RegisterUnaryTransitCallback(demand),
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
# RESULTADOS + PLANO CARTESIANO
# ============================================================

if solution:

    st.success("🚀 Optimización completada")

    resultados = []

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.set_title("Plano Logístico - CEDI Sabaneta")
    ax.set_xlabel("Longitud (Lon)")
    ax.set_ylabel("Latitud (Lat)")

    colors = ["cyan", "lime", "orange", "magenta", "yellow"]

    # CEDI
    ax.scatter(
        cedi["coord"][1],
        cedi["coord"][0],
        s=300,
        color="red"
    )
    ax.text(
        cedi["coord"][1],
        cedi["coord"][0],
        cedi["nombre"],
        color="red"
    )

    # CLIENTES
    for c in st.session_state.clientes:
        ax.scatter(c["coord"][1], c["coord"][0], s=150, color="white")
        ax.text(c["coord"][1], c["coord"][0], c["nombre"], color="white")

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

        ruta.append(cedi["nombre"])

        resultados.append({
            "Vehículo": v + 1,
            "Ruta": " → ".join(ruta),
            "Carga (kg)": carga,
            "Utilización %": round((carga / capacidad) * 100, 2),
            "Distancia km": round(distancia_total / 1000, 2)
        })

        x, y = [], []

        for p in ruta[:-1]:
            idx = nombres.index(p)
            x.append(coordenadas[idx][1])
            y.append(coordenadas[idx][0])

        x.append(cedi["coord"][1])
        y.append(cedi["coord"][0])

        ax.plot(
            x, y,
            linewidth=3,
            color=colors[v % len(colors)],
            label=f"Vehículo {v+1}"
        )

    st.subheader("📊 Resultados")
    st.dataframe(pd.DataFrame(resultados), use_container_width=True)

    st.subheader("🗺️ Plano cartesiano")
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)

else:
    st.error("❌ No se encontró solución")
