from CBSPort import TSNEgressPort
from TSNStream import TSNFrame

from parser import DestinationDataclass, StreamDataclass


class NodeType:
    END_DEVICE = "End Device"
    SWITCH = "Switch"


class Node:
    ports = dict[int, TSNEgressPort]
    type = NodeType
    receive_queue = list[tuple[int, TSNFrame]]

    def __init__(
        self,
        id: str,
        domain: int,
        ports: int = 4,
    ):
        self.id = id
        self.domain = domain
        self.ports = {i: TSNEgressPort(i) for i in range(ports)}
        self.receive_queue = []

    def receive_frame(self, frame: TSNFrame, egress_port_id: int):
        self.receive_queue.append((egress_port_id, frame))

    def step(self, global_time: float):
        pass


class Switch(Node):
    def __init__(self, id: str, domain: int, ports: int = 4):
        super().__init__(id, domain, ports)
        self.type = NodeType.SWITCH

    def step(self, global_time: float):
        # Implement switch logic to process frames and update state
        for egress_port_id, frame in self.receive_queue:
            print(f"Switch {self.id} received frame: {frame} at time {global_time}")
            self.ports[egress_port_id].receive_frame(frame, global_time)
        self.receive_queue.clear()


class EndDevice(Node):
    def __init__(self, id: str, domain: int, ports: int = 4):
        super().__init__(id, domain, ports)
        self.type = NodeType.END_DEVICE

    def step(self, global_time: float):
        # Implement end device logic to process frames and update state
        for egress_port_id, frame in self.receive_queue:
            print(f"End Device {self.id} received frame: {frame} at time {global_time}")
        self.receive_queue.clear()


if __name__ == "__main__":
    # Example usage
    switch = Switch(id="Switch1", domain=1, ports=4)

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
    frame = TSNFrame(
        stream=stream_dataclass,  # This would be a StreamDataclass instance in a real implementation
        arrival_time=0,
    )

    switch.receive_frame(frame, egress_port_id=0)
    switch.step(global_time=1.0)
    switch.ports[0].step(1)  # Process the frame in the port
