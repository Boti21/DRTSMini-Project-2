
from dataclasses import dataclass
import json
from typing import Dict, List

@dataclass 
class DestinationDataclass:
    id: str
    deadline: int
    
@dataclass 
class StreamDataclass:
    id: int
    name: str
    source: str
    destinations:List[DestinationDataclass]
    stream_type: str 
    pcp: int
    size: int
    period: int
    redundancy: int

@dataclass 
class SwitchDataclass: 
    id: str 
    ports: int
    domain: int

@dataclass 
class LinkDataclass: 
    id: str
    source: str
    destination: str
    sourcePort: int 
    destinationPort: int 
    domain: int 
    bandwidth_mbps: int
    delay: int

@dataclass
class EndSystemDataclass:
    id: str
    domain: int

@dataclass
class TopologyDataclass:
    switches: List[SwitchDataclass]
    end_systems: List[EndSystemDataclass]
    links: List[LinkDataclass]
    default_bandwidth_mbps: float
    delay_units: str

@dataclass
class PathDataclass:
    node: str
    port: int


@dataclass
class RouteDataclass:
    flow_id: int
    paths: List[List[PathDataclass]]
    min_e2e_delay_us: float    

def load_streams(path: str) -> Dict[int, StreamDataclass]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    streams = {}
    for s in raw["streams"]:
        destinations = [
            DestinationDataclass(id=d["id"], deadline=d["deadline"])
            for d in s["destinations"]
        ]

        stream = StreamDataclass(
            id=s["id"],
            name=s["name"],
            source=s["source"],
            destinations=destinations,
            stream_type=s["type"],
            pcp=s["PCP"],
            size=s["size"],
            period=s["period"],
            redundancy=s["redundancy"],
        )
        streams[stream.id] = stream

    return streams


def load_routes(path: str) -> Dict[int, RouteDataclass]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    routes = {}
    for r in raw["routes"]:
        parsed_paths = []
        for path_nodes in r["paths"]:
            hops = [PathDataclass(node=h["node"], port=h["port"]) for h in path_nodes]
            parsed_paths.append(hops)

        route = RouteDataclass(
            flow_id=r["flow_id"],
            paths=parsed_paths,
            min_e2e_delay_us=r["min_e2e_delay"],
        )
        routes[route.flow_id] = route

    return routes


def load_topology(path: str) -> TopologyDataclass:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)["topology"]

    switches = [SwitchDataclass(**sw) for sw in raw["switches"]]
    end_systems = [EndSystemDataclass(**es) for es in raw["end_systems"]]

    links = [
        LinkDataclass(
            id=l["id"],
            source=l["source"],
            destination=l["destination"],
            sourcePort=l["sourcePort"],
            destinationPort=l["destinationPort"],
            domain=l["domain"],
            bandwidth_mbps=l["bandwidth_mbps"],
            delay=l["delay"],
        )
        for l in raw["links"]
    ]

    return TopologyDataclass(
        switches=switches,
        end_systems=end_systems,
        links=links,
        default_bandwidth_mbps=raw["default_bandwidth_mbps"],
        delay_units=raw["delay_units"],
    )
