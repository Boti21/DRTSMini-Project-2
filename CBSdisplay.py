import os
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from parser import load_streams, load_topology
from TSNStream import TSNFrame
from CBSPort import TSNEgressPort


# ---------------- VISUALIZER ---------------- #

class CBSVisualizer:
    def __init__(self):
        self.time = []

        # Credits
        self.credit_A = []
        self.credit_B = []

        # Transmission trace (A/B/BE)
        self.trace = []

    def record(self, port, t):
        self.time.append(t)

        # Credits (keep this EXACTLY as you love it)
        self.credit_A.append(port.queues["A"].credit)
        self.credit_B.append(port.queues["B"].credit)

        # Which queue is transmitting
        if port.active_queue_key == "A":
            self.trace.append("A")
        elif port.active_queue_key == "B":
            self.trace.append("B")
        elif port.active_queue_key == "BE":
            self.trace.append("BE")
        else:
            self.trace.append(None)

    def plot(self):
        fig, axs = plt.subplots(
            2,
            1,
            figsize=(14, 6),
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]}  
        )

        # -----------------------
        # 1. CREDIT EVOLUTION
        # -----------------------
        axs[0].plot(self.time, self.credit_A, label="Class A Credit")
        axs[0].plot(self.time, self.credit_B, label="Class B Credit")
        axs[0].set_ylabel("Credit")
        axs[0].set_title("CBS Credit Evolution")
        axs[0].legend(loc="upper right")
        axs[0].grid()

        color_map = {
            "A": "blue",
            "B": "orange",
            "BE": "purple"
        }

        ax = axs[1]

        if len(self.time) == 0:
            return

        start_time = self.time[0]
        current_state = self.trace[0]
        interval_start = start_time

        for i in range(1, len(self.time)):
            state = self.trace[i]
            t = self.time[i]

            if state != current_state:
                ax.add_patch(
                    Rectangle(
                        (interval_start, -1),
                        self.time[i - 1] - interval_start + 1,
                        2,
                        color=color_map.get(current_state, "white"),
                        linewidth=0
                    )
                )
                interval_start = t
                current_state = state

        # close last interval
        ax.add_patch(
            Rectangle(
                (interval_start, -1),
                self.time[-1] - interval_start + 1,
                2,
                color=color_map.get(current_state, "white"),
                linewidth=0
            )
        )

        ax.set_xlim(0, self.time[-1])
        ax.set_ylim(-1, 1)
        ax.set_yticks([])
        ax.set_xlabel("Time (µs)")
        ax.set_title("CBS Transmission Timeline")

        legend = [
            Patch(facecolor="blue", label="Class A"),
            Patch(facecolor="orange", label="Class B"),
            Patch(facecolor="purple", label="Best Effort"),
        ]

        ax.legend(handles=legend, loc="upper right")
        plt.tight_layout()
        plt.show()


# ---------------- MAIN SIMULATION ---------------- #

if __name__ == "__main__":

    # Argument handling (sys)
    if len(sys.argv) != 2:
        print("Usage: python CBSdisplay.py <test_case_1>")
        sys.exit(1)

    test_case = sys.argv[1]
    test_case_dir = os.path.join("test_cases", test_case)

    if not os.path.exists(test_case_dir):
        print(f"Error: '{test_case}' does not exist.")
        print("Available options: test_case_1, test_case_2, test_case_3")
        sys.exit(1)


    # Load data
    streams = load_streams(os.path.join(test_case_dir, "streams.json"))
    topology = load_topology(os.path.join(test_case_dir, "topology.json"))

    port = TSNEgressPort(port_id=6, bandwidth_mbps=100)
    visualizer = CBSVisualizer()

    global_time = 0.0
    dt = 1.0
    SIM_TIME = 20000

    next_release = {s.id: 0 for s in streams.values()}

    print(f"Starting CBS simulation with {test_case}...")

    # Simulation loop
    while global_time < SIM_TIME:

        for s in streams.values():
            if global_time >= next_release[s.id]:
                frame = TSNFrame(
                    stream=s,
                    arrival_time=global_time
                )
                port.receive_frame(frame, global_time)
                next_release[s.id] += s.period

        port.step(dt)
        visualizer.record(port, global_time)

        global_time += dt

    print("Simulation finished. Plotting...")
    visualizer.plot()