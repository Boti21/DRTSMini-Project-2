import parser
import func
from Node import Switch, EndDevice
from TSNStream import TSNStream
from Link import Link


nodes = []
streams =[]
links = []

# for now these are here
def get_stream(streams: list, stream_id: int) -> TSNStream:
    for stream in streams:
        if stream.stream_id == stream_id:
            return stream
    raise ValueError(f"Stream with id {stream_id} not found")
        
def get_node(nodes: list, node_id: str) -> Switch | EndDevice:
    for node in nodes:
        if node.id == node_id:
            return node
    raise ValueError(f"Node with id {node_id} not found")

def get_link(links: list, link_id: str) -> Link:
    for link in links:
        if link.id == link_id:
            return link
    raise ValueError(f"Link with id {link_id} not found")


if __name__ == "__main__":

    test_case = func.load_test_case("test_cases/test_case_1")

    func.validate_test_case(test_case)

    print(test_case)

    MAX_SIMULATION_TIME_US = 1_000_000.0 # 1 second in microseconds
    global_time = 0.0 # us

    # List to make them iterable
    for node in test_case.topology.switches:
        nodes.append(Switch(id=node.id, domain=node.domain, ports=node.ports))
    for node in test_case.topology.end_systems:
        nodes.append(EndDevice(id=node.id, domain=node.domain))

    for i in test_case.streams:
        streams.append(TSNStream(test_case.streams[i]))

    for link in test_case.topology.links:
        links.append(Link(link))


    while global_time < MAX_SIMULATION_TIME_US:

        # Stepping objects
        for node in nodes:
            node.step(global_time)
        for stream in streams:
            stream.step(global_time)


        global_time += 1 # Advance by 1 us
        pass


    pass