from CBSPort import TSNEgressPort
from TSNStream import TSNFrame, TSNStream

from parser import DestinationDataclass, StreamDataclass


class NodeType:
    END_DEVICE = "End Device"
    SWITCH = "Switch"


class Node:
    ports = dict[int, TSNEgressPort]
    type = NodeType
    receive_queue = list[
        tuple[int, TSNFrame, float]
    ]  # List of (egress_port_id, frame, arrival_time)

    def __init__(
        self,
        id: str,
        domain: int,
        ports: int = 4,
        add_delay_to_wcrt: bool = False,
        delay: int = 0,
    ):
        self.id = id
        self.domain = domain
        self.ports = {i: TSNEgressPort(i) for i in range(ports)}
        self.receive_queue = []
        self.add_delay_to_wcrt = add_delay_to_wcrt
        self.current_time = 0.0
        self.delay = delay

    def receive_frame(self, frame: TSNFrame, egress_port_id: int):
        self.receive_queue.append((egress_port_id, frame, self.current_time))

    def step(self, global_time: float):
        self.current_time = global_time


class Switch(Node):
    def __init__(
        self,
        id: str,
        domain: int,
        ports: int,
        add_delay_to_wcrt: bool = False,
        delay: int = 0,
    ):
        super().__init__(id, domain, ports, add_delay_to_wcrt, delay)
        self.type = NodeType.SWITCH

    def step(self, global_time: float):
        # Implement switch logic to process frames and update state
        self.current_time = global_time
        for egress_port_id, frame, arrival_time in self.receive_queue:
            print(f"Switch {self.id} received frame: {frame} at time {global_time}")
            if (
                not (self.add_delay_to_wcrt)
                or self.current_time - arrival_time >= self.delay
            ):
                print(
                    f"Switch {self.id} processing frame: {frame} at time {global_time}"
                )
                self.ports[egress_port_id].receive_frame(frame, global_time)
                self.receive_queue.remove((egress_port_id, frame, arrival_time))


class EndDevice(Node):
    wcrts = dict[int, float]  # Worst-case response times for each stream ID

    def __init__(
        self,
        id: str,
        domain: int,
        ports: int = 0,
        add_delay_to_wcrt: bool = False,
        delay: int = 0,
    ):
        super().__init__(id, domain, ports, add_delay_to_wcrt, delay)
        self.type = NodeType.END_DEVICE
        self.send_queue = list[tuple[TSNFrame, float]]  # Queue of frames to send

    def send_frame(self, frame: TSNFrame):
        self.send_queue.append((frame, self.current_time))

    def step(self, global_time: float):
        # Implement end device logic to process frames and update state
        self.current_time = global_time
        for egress_port_id, frame, arrival_time in self.receive_queue:
            print(f"End Device {self.id} received frame: {frame} at time {global_time}")
            self.wcrts[frame.stream.id] = global_time - arrival_time
        self.receive_queue.clear()

        # Process frames in the send queue
        for frame, arrival_time in self.send_queue:
            if (
                not (self.add_delay_to_wcrt)
                or self.current_time - arrival_time >= self.delay
            ):
                print(
                    f"End Device {self.id} sending frame: {frame} at time {global_time}"
                )
                self.ports[0].receive_frame(
                    frame, global_time
                )  # Assuming port 0 is used for sending
                self.send_queue.remove((frame, arrival_time))

    def get_wcrts(self) -> dict[int, float]:
        return self.wcrts


if __name__ == "__main__":
    # Example usage
    switch = Switch(id="Switch1", domain=1, ports=4, add_delay_to_wcrt=True, delay=5)

    stream_dataclass = StreamDataclass(
        id=1,
        name="Test Stream",
        source="EndDevice1",
        destinations=[DestinationDataclass(id="EndDevice2", deadline=100)],
        stream_type="TypeA",
        pcp=3,
        size=1500,
        period=1000,
        redundancy=1,
    )
    stream = TSNStream(stream_dataclass)
    frame = TSNFrame(
        stream=stream,
        arrival_time=0,
    )

    switch.receive_frame(frame, egress_port_id=0)
    for time in range(0, 20, 1):
        switch.step(global_time=time)
    switch.ports[0].step(1)  # Process the frame in the port
