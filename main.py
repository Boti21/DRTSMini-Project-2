import parser
import random
import func
from Node import Switch, EndDevice
from TSNStream import TSNStream
from Link import Link
from lookup_tables import get_stream, get_node, get_link, links, nodes, streams
from analysis.Analysis import Analyzer

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="TSN Simulator")
    parser.add_argument(
        "--test-case",
        type=str,
        default="test_cases/test_case_0",
        help="Path to the test case directory (default: test_cases/test_case_0)",
    )
    parser.add_argument(
        "--max-simulation-time",
        type=float,
        default=1_000.0,
        help="Maximum simulation time in microseconds (default: 1,000 us = 1 second)",
    )
    return parser.parse_args()

if __name__ == "__main__":

    args = parse_args()
    test_case = func.load_test_case(args.test_case)
    MAX_SIMULATION_TIME_US = args.max_simulation_time

    routes = func.load_routes(f"{args.test_case}/routes.json")

    func.validate_test_case(test_case)

    # print(test_case)

    global_time = 0.0  # us

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
        print(
            f"{links[i].id} | {links[i].source_port} -> {links[i].destination_port} | {links[i].source} -> {links[i].destination} | delay={links[i].delay}us"
        )

        source_node = get_node(links[i].source)

        if source_node.type == "End Device":
            print(f"Source node {links[i].source} is an End Device")
            source_node.ports[links[i].source_port].add_link(links[i])
        else:
            print(f"Source node {links[i].source} is a Switch")
            source_node.ports[links[i].source_port].add_link(links[i])
            print(f"Source node: {source_node.id} | n ports: {len(source_node.ports)}")

    analizer = Analyzer()
    analizer.analyze_all(routes=routes, streams=streams)
    print(f"Analysis complete")
    for i, wcrt in analizer.wcrts.items():
        print(f"WCRT for stream {i}: {wcrt}")

    wcrts = {}
    for i in range(1000):
        while global_time < MAX_SIMULATION_TIME_US:

            # Stepping objects
            for node in nodes:
                node.step(global_time)
                for port in node.ports:
                    node.ports[port].step(1)
            permuted_streams = list(streams)
            random.shuffle(permuted_streams)
            for stream in permuted_streams:
                stream.step(global_time)
            for link in links:
                link.step(global_time)

            global_time += 1  # Advance by 1 us
            pass

        for end_device in nodes:
            if end_device.type == "End Device":
                for stream_id, wcrt in end_device.wcrts.items():
                    if stream_id not in wcrts:
                        wcrts[stream_id] = 0
                    wcrts[stream_id] = max(wcrts[stream_id], wcrt)

    print("Simulation finished")

    print("")

    print("Worst-case response times:")

    for stream_id, wcrt in wcrts.items():
        print(f"Stream {stream_id}: {wcrt} us")

    pass
