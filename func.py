from dataclasses import dataclass
from pathlib import Path as FilePath
from typing import Dict, List, Tuple

from parser import Link, Path, Route, Stream, Topology, load_routes, load_streams, load_topology


@dataclass
class TestCase:
    streams: Dict[int, Stream]
    routes: Dict[int, Route]
    topology: Topology


def load_test_case(folder_path: str | FilePath) -> TestCase:
    folder = FilePath(folder_path)

    streams = load_streams(folder / "streams.json")
    routes = load_routes(folder / "routes.json")
    topology = load_topology(folder / "topology.json")

    return TestCase(
        streams=streams,
        routes=routes,
        topology=topology,
    )


def build_link_index(topology: Topology):
    index = {}

    for link in topology.links:
        key = (link.source, link.sourcePort, link.destination)
        index[key] = link

    return index

def route_path_to_links(path: List[Path], link_index) -> List[Link]:
    links = []

    for i in range(len(path) - 1):
        current_hop = path[i]
        next_hop = path[i + 1]

        key = (current_hop.node, current_hop.port, next_hop.node)

        if key not in link_index:
            raise ValueError(f"No link found for segment {key}")

        links.append(link_index[key])

    return links

def pcp_to_traffic_class(pcp: int) -> str:
    if pcp == 2:
        return "AVB_A"
    if pcp == 1:
        return "AVB_B"
    if pcp == 0:
        return "BE"
    raise ValueError(f"Unsupported PCP value: {pcp}")


def validate_test_case(test_case: TestCase) -> None:
    streams = test_case.streams
    routes = test_case.routes
    topology = test_case.topology

    node_ids = {sw.id for sw in topology.switches} | {es.id for es in topology.end_systems}
    link_index = build_link_index(topology)

    for stream_id, stream in streams.items():
        if stream_id not in routes:
            raise ValueError(f"Missing route for stream {stream_id}")

        route = routes[stream_id]
        destination_ids = {d.id for d in stream.destinations}

        if not route.paths:
            raise ValueError(f"Route for stream {stream_id} has no paths")

        for path in route.paths:
            if not path:
                raise ValueError(f"Route for stream {stream_id} contains an empty path")

            if path[0].node != stream.source:
                raise ValueError(
                    f"Route for stream {stream_id} starts at {path[0].node}, expected {stream.source}"
                )

            if path[-1].node not in destination_ids:
                raise ValueError(
                    f"Route for stream {stream_id} ends at {path[-1].node}, expected one of {destination_ids}"
                )

            for hop in path:
                if hop.node not in node_ids:
                    raise ValueError(
                        f"Unknown node {hop.node} found in path of stream {stream_id}"
                    )

            for i in range(len(path) - 1):
                current_hop = path[i]
                next_hop = path[i + 1]
                key = (current_hop.node, current_hop.port, next_hop.node)
                if key not in link_index:
                    raise ValueError(
                        f"No topology link matches route segment {key} for stream {stream_id}"
                        )


def get_stream_links(test_case: TestCase, stream_id: int) -> List[Link]:
    if stream_id not in test_case.streams:
        raise ValueError(f"Unknown stream id {stream_id}")

    if stream_id not in test_case.routes:
        raise ValueError(f"No route found for stream id {stream_id}")

    route = test_case.routes[stream_id]
    if not route.paths:
        raise ValueError(f"Route for stream {stream_id} has no paths")

    link_index = build_link_index(test_case.topology)
    return route_path_to_links(route.paths[0], link_index)


if __name__ == "__main__":
    test_case = load_test_case("test_cases/test_case_1")

    validate_test_case(test_case)

    print(f"Loaded {len(test_case.streams)} streams")
    print(f"Loaded {len(test_case.routes)} routes")
    print(f"Loaded {len(test_case.topology.links)} links")
    print()

    for stream_id, stream in test_case.streams.items():
        route = test_case.routes[stream_id]
        traffic_class = pcp_to_traffic_class(stream.pcp)
        route_links = get_stream_links(test_case, stream_id)

        print(
            f"Stream {stream.id} | "
            f"class={traffic_class} | "
            f"source={stream.source} | "
            f"dest={stream.destinations[0].id} | "
            f"size={stream.size}B | "
            f"period={stream.period}us | "
            f"links={[link.id for link in route_links]}"
        )
