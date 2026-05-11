import matplotlib.pyplot as plt
import networkx as nx
import random
import sys
import os

from parser import load_routes
from func import load_test_case
from Node import Switch, EndDevice
from TSNStream import TSNStream
from Link import Link
from lookup_tables import nodes, streams, links
from analysis.Analysis import Analyzer


# -------------------------
# STREAM COLOR MAP
# -------------------------
def get_stream_colors(stream_ids):
    palette = [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7",
        "#9C755F", "#BAB0AC", "#2F4B7C", "#A05195",
        "#D37295", "#6B8E23", "#17A2B8"
    ]

    stream_ids = sorted(stream_ids)

    return {
        sid: palette[i % len(palette)]
        for i, sid in enumerate(stream_ids)
    }


# -------------------------
# TOPOLOGY PLOT
# -------------------------
def plot_topology(ax, topology, routes, stream_colors):

    G = nx.DiGraph()

    for sw in topology.switches:
        G.add_node(sw.id, type="switch")

    for es in topology.end_systems:
        G.add_node(es.id, type="end_system")

    for link in topology.links:
        G.add_edge(
            link.source,
            link.destination,
            id=link.id,
            delay=link.delay,
            bandwidth=link.bandwidth_mbps
        )

    pos = nx.spring_layout(G, seed=42)

    switches = [n for n, d in G.nodes(data=True) if d["type"] == "switch"]
    ends = [n for n, d in G.nodes(data=True) if d["type"] == "end_system"]

    nx.draw_networkx_nodes(G, pos, nodelist=switches,
                           node_color="orange", node_size=800, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=ends,
                           node_color="skyblue", node_size=800, ax=ax)

    nx.draw_networkx_edges(G, pos, edge_color="lightgray",
                           arrows=True, arrowstyle="->", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, ax=ax)

    # -------------------------
    # STREAM ROUTES
    # -------------------------
    if routes:
        legend_handles = []

        for idx, (stream_id, route) in enumerate(routes.items()):

            color = stream_colors.get(stream_id, "black")

            try:
                route_nodes = [hop.node for hop in route.paths[0]]
            except Exception:
                continue

            if len(route_nodes) < 2:
                continue

            route_edges = list(zip(route_nodes[:-1], route_nodes[1:]))

            rad = 0.15 * ((idx % 5) - 2)

            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=route_edges,
                width=1.5,
                edge_color=[color],
                arrows=True,
                arrowstyle="->",
                arrowsize=18,
                ax=ax,
                connectionstyle=f"arc3,rad={rad}"
            )

            legend_handles.append(
                plt.Line2D([0], [0], color=color, lw=3,
                           label=f"Stream {stream_id}")
            )

        if legend_handles:
            ax.legend(
                handles=legend_handles,
                loc="upper right",
                fontsize="small",
                frameon=True,
                framealpha=0.9
            )

    ax.set_title("Topology")


# -------------------------
# WCRT COMPARISON PLOT
# -------------------------
def plot_wcrts(ax, sim_wcrts, ana_wcrts, sim_time, stream_colors):

    stream_ids = sorted(set(list(sim_wcrts.keys()) + list(ana_wcrts.keys())))

    sim_vals = [sim_wcrts.get(sid, 0) for sid in stream_ids]
    ana_vals = [ana_wcrts.get(sid, 0) for sid in stream_ids]

    colors = [stream_colors.get(sid, "black") for sid in stream_ids]

    x = range(len(stream_ids))

    # Analytical (background)
    ax.bar(
        x,
        ana_vals,
        color=colors,
        alpha=0.25,
        width=0.6,
        label="Analytical WCRT",
        zorder=1
    )

    # Simulated (front)
    bars = ax.bar(
        x,
        sim_vals,
        color=colors,
        width=0.6,
        label="Simulated WCRT",
        zorder=2
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels([str(sid) for sid in stream_ids])

    ax.set_xlabel("Stream ID")
    ax.set_ylabel("WCRT (µs)")
    ax.set_title(f"WCRTs (Sim_time = {int(sim_time)} µs)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    max_val = max(max(sim_vals, default=0), max(ana_vals, default=0))
    ax.set_ylim(0, max_val * 1.1 if max_val > 0 else 1)

    for i, bar in enumerate(bars):
        val = sim_vals[i]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_val * 0.02,
            f"{val:.0f}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    ax.legend()


# -------------------------
# SIMULATION
# -------------------------
def run_simulation(test_case_dir, max_sim_time=1000.0):

    test_case = load_test_case(test_case_dir)
    routes = load_routes(os.path.join(test_case_dir, "routes.json"))

    nodes.clear()
    streams.clear()
    links.clear()

    for node in test_case.topology.switches:
        nodes.append(Switch(id=node.id, domain=node.domain, ports=node.ports))

    for node in test_case.topology.end_systems:
        nodes.append(EndDevice(id=node.id, domain=node.domain))

    for i in test_case.streams:
        streams.append(TSNStream(test_case.streams[i]))

    for link in test_case.topology.links:
        links.append(Link(link))

    for link in links:
        source_node = next((n for n in nodes if n.id == link.source), None)
        if source_node:
            source_node.ports[link.source_port].add_link(link)

    analyzer = Analyzer()
    analyzer.analyze_all(routes=routes, streams=streams)

    print("Analytical WCRTs:")
    for i, wcrt in analyzer.wcrts.items():
        print(f"Stream {i}: {wcrt} µs")

    global_time = 0.0
    sim_wcrts = {}

    while global_time < max_sim_time:

        for node in nodes:
            node.step(global_time)
            for port_id in node.ports:
                node.ports[port_id].step(1)

        shuffled = list(streams)
        random.shuffle(shuffled)

        for stream in shuffled:
            stream.step(global_time)

        for link in links:
            link.step(global_time)

        global_time += 1

    for end_device in nodes:
        if end_device.type == "End Device":
            for sid, wcrt in end_device.wcrts.items():
                sim_wcrts[sid] = max(sim_wcrts.get(sid, 0), wcrt)

    print("Simulated WCRTs:")
    for sid, wcrt in sim_wcrts.items():
        print(f"Stream {sid}: {wcrt} µs")

    return test_case.topology, routes, sim_wcrts, analyzer.wcrts


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python plot_topology.py <test_case_name|test_all> [max_sim_time]")
        sys.exit(1)

    mode = sys.argv[1]
    max_sim_time = float(sys.argv[2]) if len(sys.argv) > 2 else 1000.0


    def run_case(test_case_name):
        test_case_dir = os.path.join("test_cases", test_case_name)

        topology, routes, sim_wcrts, ana_wcrts = run_simulation(
            test_case_dir, max_sim_time
        )

        stream_ids = set(list(routes.keys()) + list(sim_wcrts.keys()) + list(ana_wcrts.keys()))
        stream_colors = get_stream_colors(stream_ids)

        return topology, routes, sim_wcrts, ana_wcrts, stream_colors


    if mode == "test_all":

        cases = [f"test_case_{i}" for i in range(4)]

        fig, axes = plt.subplots(
            nrows=4,
            ncols=2,
            figsize=(12, 16)
        )

        fig.suptitle("All Test Cases", fontsize=16, fontweight="bold")

        for i, case in enumerate(cases):

            topology, routes, sim_wcrts, ana_wcrts = run_simulation(
                os.path.join("test_cases", case),
                max_sim_time
            )

            stream_ids = set(list(routes.keys()) + list(sim_wcrts.keys()) + list(ana_wcrts.keys()))
            stream_colors = get_stream_colors(stream_ids)

            plot_topology(axes[i, 0], topology, routes, stream_colors)

            plot_wcrts(
                axes[i, 1],
                sim_wcrts,
                ana_wcrts,
                max_sim_time,
                stream_colors
            )

        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.show()

    else:

        topology, routes, sim_wcrts, ana_wcrts, stream_colors = run_case(mode)

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        fig.suptitle(mode, fontsize=14, fontweight="bold")

        plot_topology(axes[0], topology, routes, stream_colors)

        plot_wcrts(
            axes[1],
            sim_wcrts,
            ana_wcrts,
            max_sim_time,
            stream_colors
        )

        plt.tight_layout()
        plt.show()