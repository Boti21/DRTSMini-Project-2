import parser
import func
from Node import Switch, EndDevice
from TSNStream import TSNStream
from Link import Link
from lookup_tables import get_stream, get_node, get_link, links, nodes, streams
from analysis.Analysis import Analyzer

if __name__ == "__main__":

    test_case = func.load_test_case("test_cases/test_case_1")

    func.validate_test_case(test_case)

    # print(test_case)

    # MAX_SIMULATION_TIME_US = 1_000_000.0 # 1 second in microseconds
    MAX_SIMULATION_TIME_US = 1000.0
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
    
    for i in range(len(links)):
        print(f"i: {i}")
        print(f"{links[i].id} | {links[i].source_port} -> {links[i].destination_port} | {links[i].source} -> {links[i].destination} | delay={links[i].delay}us")

        source_node = get_node(links[i].source)

        if(source_node.type == "End Device"):
            print(f"Source node {links[i].source} is an End Device")
            source_node.ports[links[i].source_port].add_link(links[i])
        else:
            print(f"Source node {links[i].source} is a Switch")
            source_node.ports[links[i].source_port].add_link(links[i])
            print(f"Source node: {source_node.id} | n ports: {len(source_node.ports)}")

    analizer = Analyzer()
    analizer.wcrt_cal(route=nodes, stream=streams[0])
    print(f"Analysis complete. WCRT: {analizer.wcrt}")

    while global_time < MAX_SIMULATION_TIME_US:

        # Stepping objects
        for node in nodes:
            node.step(global_time)
            for port in node.ports:
                node.ports[port].step(1)
        for stream in streams:
            stream.step(global_time)


        global_time += 1 # Advance by 1 us
        pass

    print("Simulation finished")

    pass
