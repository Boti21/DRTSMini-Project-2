import json
import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import gridspec
from matplotlib.ticker import MaxNLocator

from parser import load_streams, load_topology, load_routes
from TSNStream import TSNFrame, TSNStream
from CBSPort import TSNEgressPort

# =========================================================
# LOAD DATA
# =========================================================

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_wcrts(path):
    if not os.path.isfile(path):
        return {}

    wcrts = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            try:
                stream_id = int(parts[0])
                wcrts[stream_id] = float(parts[1].replace(",", "."))
            except ValueError:
                continue

    return wcrts


if len(sys.argv) not in (2, 3):
    print("Usage: python CBSdisplay_v2.py test_case_X [SIM_TIME]")
    sys.exit(1)

case_name = sys.argv[1]

if len(sys.argv) == 3:
    try:
        SIM_TIME = float(sys.argv[2])
    except ValueError:
        print("Error: SIM_TIME must be a number.")
        sys.exit(1)
else:
    SIM_TIME = 5000


test_case_dir = os.path.join("test_cases", case_name)

if not os.path.isdir(test_case_dir):
    print(f"Error: test case directory '{test_case_dir}' does not exist.")
    sys.exit(1)

routes = load_routes(os.path.join(test_case_dir, "routes.json"))
streams = load_streams(os.path.join(test_case_dir, "streams.json"))
topology_json = load_json(os.path.join(test_case_dir, "topology.json"))
reference_wcrts = load_wcrts(os.path.join(test_case_dir, "WCRTs.csv"))

if reference_wcrts:
    print("Loaded reference WCRTs from WCRTs.csv:")
    for stream_id, wcrt in sorted(reference_wcrts.items()):
        print(f"  Stream {stream_id}: {wcrt} µs")

# =========================================================
# COLORS (GLOBAL CONSISTENCY)
# =========================================================

COLORS = {
    "A": "blue",
    "B": "orange",
    "BE": "purple",
    "NA": "white"
}


def encode_class(q):
    if q == "A":
        return 2
    if q == "B":
        return 1
    if q == "BE":
        return 0
    return -1


def decode_class(x):
    return {2: "A", 1: "B", 0: "BE"}.get(x, "NA")

# =========================================================
# GRAPH BUILD
# =========================================================

G = nx.DiGraph()

topology = topology_json["topology"]

nodes = [sw["id"] for sw in topology["switches"]] + [es["id"] for es in topology["end_systems"]]
G.add_nodes_from(nodes)

link_labels = {}

for link in topology["links"]:
    link_bandwidth = link.get("bandwidth_mbps", topology.get("default_bandwidth_mbps", 100))
    G.add_edge(
        link["source"],
        link["destination"],
        id=link["id"],
        bandwidth=link_bandwidth,
        delay=link["delay"],
        source_port=link["sourcePort"],
        destination_port=link["destinationPort"],
    )
    link_labels[(link["source"], link["destination"])] = (
        f"{link['id']}"
    )

pos = {
    "SW0": (0, 1),
    "SW1": (1, 1),
    "ES0": (1, 0),
    "ES1": (0, 0)
}

# =========================================================
# CBS PORTS
# =========================================================

default_bandwidth = topology.get("default_bandwidth_mbps", 100)

switch_ports = {
    "SW0": TSNEgressPort(port_id=2, bandwidth_mbps=default_bandwidth, switch_name="SW0"),
    "SW1": TSNEgressPort(port_id=6, bandwidth_mbps=default_bandwidth, switch_name="SW1"),
}

# =========================================================
# DATA STORAGE
# =========================================================

cbs_data = {
    "SW0": {"t": [], "A": [], "B": [], "queue_A": [], "queue_B": [], "queue_BE": [], "tx_class": [], "frame_id": []},
    "SW1": {"t": [], "A": [], "B": [], "queue_A": [], "queue_B": [], "queue_BE": [], "tx_class": [], "frame_id": []}
}

frame_counter = 0

# =========================================================
# SIMULATION
# =========================================================

global_time = 0.0
dt = 1.0
next_release = {s.id: 0 for s in streams.values()}

print(f"Running CBS simulation for {case_name}...")

while global_time < SIM_TIME:

    # -----------------------------------------------------
    # FRAME GENERATION + ROUTING
    # -----------------------------------------------------
    for s in streams.values():
        s = TSNStream(s)

        if global_time >= next_release[s.stream_id]:
            frame = TSNFrame(stream=s, arrival_time=global_time)
            frame.instance_id = frame_counter
            frame_counter += 1

            if s.stream_id in routes:
                route = routes[s.stream_id]
                path = route.paths[0]

                if len(path) > 1:
                    first_switch = path[1].node
                    if first_switch in switch_ports:
                        switch_ports[first_switch].receive_frame(frame, global_time)

            next_release[s.stream_id] += s.period

    # -----------------------------------------------------
    # CBS UPDATE
    # -----------------------------------------------------
    for sw_name, port in switch_ports.items():
        port.step(dt)

        cbs_data[sw_name]["t"].append(global_time)
        cbs_data[sw_name]["A"].append(port.queues["A"].credit)
        cbs_data[sw_name]["B"].append(port.queues["B"].credit)
        cbs_data[sw_name]["queue_A"].append(len(port.queues["A"].buffer))
        cbs_data[sw_name]["queue_B"].append(len(port.queues["B"].buffer))
        cbs_data[sw_name]["queue_BE"].append(len(port.queues["BE"].buffer))
        cbs_data[sw_name]["tx_class"].append(encode_class(port.active_queue_key))
        cbs_data[sw_name]["frame_id"].append(
            port.current_frame.instance_id if port.current_frame is not None else -1
        )

    global_time += dt

print("CBS simulation complete.")

# =========================================================
# HELPERS (GANTT)
# =========================================================

def build_intervals(t, frame_ids, classes):
    intervals = []
    if not t:
        return intervals

    start = t[0]
    current_frame = frame_ids[0]
    current_class = classes[0]

    for i in range(1, len(t)):
        if frame_ids[i] != current_frame:
            if current_frame != -1:
                intervals.append((start, t[i], current_class))
            start = t[i]
            current_frame = frame_ids[i]
            current_class = classes[i]

    if current_frame != -1:
        intervals.append((start, t[-1] + 1, current_class))

    return intervals


def plot_gantt(ax, intervals, title):
    y_positions = {"A": 2, "B": 1, "BE": 0}

    for start, end, cls in intervals:
        if cls not in y_positions:
            continue

        ax.barh(
            y_positions[cls],
            end - start,
            left=start,
            height=0.7,
            color=COLORS.get(cls, "black"),
            edgecolor="black",
            alpha=0.8
        )

    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels(["A", "B", "BE"])
    ax.set_ylim(-0.5, 2.5)
    ax.set_xlabel("Time (µs)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)

# =========================================================
# PLOTTING LAYOUT (TRANSMISSION BEFORE QUEUES)
# =========================================================

fig = plt.figure(figsize=(16, 8))

gs = gridspec.GridSpec(
    3, 3,
    width_ratios=[1.5, 1.5, 1.5],
    height_ratios=[1.2, 1.2, 1.2]
)

ax_net = fig.add_subplot(gs[0:2, 0])
ax_sw0 = fig.add_subplot(gs[0, 1])
ax_sw1 = fig.add_subplot(gs[0, 2])

ax_tx0 = fig.add_subplot(gs[1, 1])
ax_tx1 = fig.add_subplot(gs[1, 2])

ax_q0 = fig.add_subplot(gs[2, 1])
ax_q1 = fig.add_subplot(gs[2, 2])

# =========================================================
# NETWORK
# =========================================================

def draw():
    ax_net.clear()
    nx.draw_networkx_nodes(G, pos, node_size=1800, node_color="lightblue", ax=ax_net)
    nx.draw_networkx_labels(G, pos, ax=ax_net)
    nx.draw_networkx_edges(G, pos, arrows=True, ax=ax_net)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=link_labels, ax=ax_net)

draw()
ax_net.set_title(f"Topology - {case_name}")

# =========================================================
# CBS CREDITS
# =========================================================

ax_sw0.plot(cbs_data["SW0"]["t"], cbs_data["SW0"]["A"], color=COLORS["A"], label="A Credit")
ax_sw0.plot(cbs_data["SW0"]["t"], cbs_data["SW0"]["B"], color=COLORS["B"], label="B Credit")
ax_sw0.set_title("SW0 Credits")
ax_sw0.set_xlabel("Time (µs)")
ax_sw0.set_xlim(0, SIM_TIME)
ax_sw0.grid()
ax_sw0.legend()

ax_sw1.plot(cbs_data["SW1"]["t"], cbs_data["SW1"]["A"], color=COLORS["A"], label="A Credit")
ax_sw1.plot(cbs_data["SW1"]["t"], cbs_data["SW1"]["B"], color=COLORS["B"], label="B Credit")
ax_sw1.set_title("SW1 Credits")
ax_sw1.set_xlabel("Time (µs)")
ax_sw1.set_xlim(0, SIM_TIME)
ax_sw1.grid()
ax_sw1.legend()

# =========================================================
# TRANSMISSION (GANTT)
# =========================================================

sw0_classes = [decode_class(x) for x in cbs_data["SW0"]["tx_class"]]
sw1_classes = [decode_class(x) for x in cbs_data["SW1"]["tx_class"]]

sw0_intervals = build_intervals(
    cbs_data["SW0"]["t"],
    cbs_data["SW0"]["frame_id"],
    sw0_classes
)

sw1_intervals = build_intervals(
    cbs_data["SW1"]["t"],
    cbs_data["SW1"]["frame_id"],
    sw1_classes
)

plot_gantt(ax_tx0, sw0_intervals, "SW0 Transmission")
ax_tx0.set_xlim(0, SIM_TIME)

plot_gantt(ax_tx1, sw1_intervals, "SW1 Transmission")
ax_tx1.set_xlim(0, SIM_TIME)

# =========================================================
# QUEUES
# =========================================================

ax_q0.plot(cbs_data["SW0"]["t"], cbs_data["SW0"]["queue_A"], color=COLORS["A"], label="A")
ax_q0.plot(cbs_data["SW0"]["t"], cbs_data["SW0"]["queue_B"], color=COLORS["B"], label="B")
ax_q0.plot(cbs_data["SW0"]["t"], cbs_data["SW0"]["queue_BE"], color=COLORS["BE"], label="BE")
ax_q0.set_title("SW0 Queues")
ax_q0.set_xlabel("Time (µs)")
ax_q0.set_xlim(0, SIM_TIME)
ax_q0.yaxis.set_major_locator(MaxNLocator(integer=True, min_n_ticks=1))
ax_q0.grid()
ax_q0.legend()

ax_q1.plot(cbs_data["SW1"]["t"], cbs_data["SW1"]["queue_A"], color=COLORS["A"], label="A")
ax_q1.plot(cbs_data["SW1"]["t"], cbs_data["SW1"]["queue_B"], color=COLORS["B"], label="B")
ax_q1.plot(cbs_data["SW1"]["t"], cbs_data["SW1"]["queue_BE"], color=COLORS["BE"], label="BE")
ax_q1.set_title("SW1 Queues")
ax_q1.set_xlabel("Time (µs)")
ax_q1.set_xlim(0, SIM_TIME)
ax_q1.yaxis.set_major_locator(MaxNLocator(integer=True, min_n_ticks=1))
ax_q1.grid()
ax_q1.legend()

plt.tight_layout()
plt.show()