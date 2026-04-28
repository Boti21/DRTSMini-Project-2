import collections
import os
from Link import Link
from TSNStream import TSNStream, TSNFrame

from parser import load_streams, load_topology


class CBSQueue:
    """Helper class to manage individual AVB/BE queues within a port."""

    def __init__(self, queue_id, shaper_type, idle_slope_bps=0, port_bw_bps=0):
        self.queue_id = queue_id
        self.shaper_type = shaper_type  # "CBS" or "SP" (Strict Priority)
        self.buffer = collections.deque()

        # CBS Specifics (Slopes are bits per microsecond)
        self.credit = 0.0
        self.idle_slope = idle_slope_bps / 1_000_000
        self.send_slope = (idle_slope_bps - port_bw_bps) / 1_000_000

        self.is_transmitting = False

    def has_frames(self):
        return len(self.buffer) > 0


class TSNEgressPort:
    """
    The Egress Port Module.
    Abstracted as a component that processes logic in discrete steps (dt).
    """

    link: Link = (
        None  # This will be set by the main simulator when connecting the port to a link
    )

    def __init__(
        self,
        port_id,
        bandwidth_mbps=100,
        class_a_idle_fraction=0.5,
        class_b_idle_fraction=0.5,
        link=None,
    ):
        self.port_id = port_id
        self.bandwidth_bps = bandwidth_mbps * 1_000_000

        class_a_idle_slope_bps = class_a_idle_fraction * self.bandwidth_bps
        class_b_idle_slope_bps = class_b_idle_fraction * self.bandwidth_bps

        # Initialize the 3 required queues
        # Note: In real scenarios, slopes come from switch_config.json.
        # For the simplified test-case setting, defaults are 0.5 for both A and B.
        self.queues = {
            "A": CBSQueue("A", "CBS", class_a_idle_slope_bps, self.bandwidth_bps),
            "B": CBSQueue("B", "CBS", class_b_idle_slope_bps, self.bandwidth_bps),
            "BE": CBSQueue("BE", "SP"),  # Best Effort
        }

        self.pcp_to_queue = {
            2: "A",  # Maps to the CBS Queue for Class A
            1: "B",  # Maps to the CBS Queue for Class B
            0: "BE",  # Maps to the Strict Priority Queue
        }

        # Link State
        self.is_busy = False
        self.remaining_trans_time = 0.0
        self.current_frame = None
        self.active_queue_key = None

    def receive_frame(self, frame, current_time):
        """Called by the Switch/Global Sim when a frame arrives at this port."""
        frame.arrival_time = current_time
        target_queue = self.pcp_to_queue.get(frame.pcp, "BE")

        self.queues[target_queue].buffer.append(frame)

    def add_link(self, link: Link):
        """Associate a Link with this port for frame delivery."""
        self.link = link

    def step(self, dt):
        """
        The main simulation tick.
        dt = time increment in microseconds.
        """
        finished_frame = None

        # 1. Update Link Progress
        if self.is_busy:
            self.remaining_trans_time -= dt
            # Update credit for the queue currently occupying the wire
            q = self.queues[self.active_queue_key]
            if q.shaper_type == "CBS":
                q.credit += q.send_slope * dt

            if self.remaining_trans_time <= 0:
                finished_frame = self.current_frame
                self.queues[self.active_queue_key].is_transmitting = False
                self.is_busy = False
                self.current_frame = None
                self.active_queue_key = None

        # 2. Update Credits for Waiting Queues
        for key in ["A", "B"]:
            q = self.queues[key]
            if not q.is_transmitting:
                if q.has_frames():
                    # Waiting for high priority or credit recovery
                    q.credit += q.idle_slope * dt
                else:
                    # Empty queue: Credit must move toward 0
                    if q.credit > 0:
                        q.credit = 0  # IEEE 802.1Qav: positive credit resets if empty
                    elif q.credit < 0:
                        q.credit = min(0, q.credit + q.idle_slope * dt)

        # 3. Transmission Selection (Scheduling)
        if not self.is_busy:
            # Check Priorities in Order: A -> B -> BE
            selected_key = None

            # Check AVB Class A
            if self.queues["A"].has_frames() and self.queues["A"].credit >= 0:
                selected_key = "A"
            # Check AVB Class B
            elif self.queues["B"].has_frames() and self.queues["B"].credit >= 0:
                selected_key = "B"
            # Check Best Effort (Strict Priority)
            elif self.queues["BE"].has_frames():
                selected_key = "BE"

            if selected_key:
                q = self.queues[selected_key]
                self.is_busy = True
                self.active_queue_key = selected_key
                self.current_frame = q.buffer.popleft()
                q.is_transmitting = True
                # Duration in microseconds = bits / (bits per microsecond)
                self.remaining_trans_time = (self.current_frame.size_bytes * 8) / (
                    self.bandwidth_bps / 1_000_000
                )

        if finished_frame:
            if self.link:
                self.link.receive_frame(finished_frame)
                print(f"Finished frame transmitted through link: {finished_frame}")
            else:
                # Visualization mode (no link attached)
                pass
                # Optional debug:
                # print(f"Finished frame (no link): {finished_frame}")

# --- SIMULATOR EXAMPLE ---

if __name__ == "__main__":
    # Resolve the test-case folder naming used in this repo.
    candidate_dirs = ["test_cases/test_case_1"]
    test_case_dir = next((d for d in candidate_dirs if os.path.isdir(d)), None)
    if test_case_dir is None:
        raise FileNotFoundError(
            "Could not find a test case directory. Tried: " + ", ".join(candidate_dirs)
        )

    streams = load_streams(os.path.join(test_case_dir, "streams.json"))
    topology = load_topology(os.path.join(test_case_dir, "topology.json"))

    # 1. Setup Port - This will have to be handled by the main simulator!!!
    my_port = TSNEgressPort(
        port_id=1,
        bandwidth_mbps=topology.default_bandwidth_mbps,
    )

    link_data = topology.links[0]  # Just take the first link for this example
    my_link = Link(link_data)
    my_port.add_link(my_link)
    global_time = 0.0
    tick_size = 1.0  # 1 microsecond steps

    # This will have to be handled by the main simulator also!!!
    frames = []
    for stream in streams.values():
        frame = TSNFrame(
            stream=stream,  
            arrival_time=0,  # This will be set to the global time when the frame is sent to the port
        )
        frames.append(frame)

    for frame in frames:
        print(frame)
        my_port.receive_frame(
            frame, global_time
        )  # In this implementation, a frame's arrival_time member is set to the global time (simulates simulator's time)
        # This way, we can then simply compare the simulation time after processing the frame and get the "local" time spent in the port.
        # I could add this time to the end-to-end delay if the main simulator provides it to me, otherwise, I can return this local time
        # and let the simulator handle it.

    for _ in range(3000000):
        out = my_port.step(tick_size)
        if out:
            delay = global_time - out.arrival_time
            print(f"Time {global_time}: {out} finished! End-to-End Delay: {delay}us")
            print(f"--- Class A Credit at finish: {my_port.queues['A'].credit:.2f}")
            print(f"--- Class B Credit at finish: {my_port.queues['B'].credit:.2f}\n")

        global_time += tick_size
