from CBSPort import TSNEgressPort, TSNFrame
import abc


class NodeType:
    END_DEVICE = "End Device"
    SWITCH = "Switch"


@abc.ABCMeta
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

    @abc.abstractmethod
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
            self.ports[egress_port_id].send_frame(frame)
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
