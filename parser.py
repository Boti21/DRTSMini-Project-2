
from dataclasses import dataclass
import json
from typing import Dict, List

@dataclass 
class Destination:
    id: str
    deadline: int
    
@dataclass 
class Stream:
    id: int
    name: str
    source: str
    destinations:List[Destination]
    stream_type: str 
    pcp: int
    size: int
    period: int
    redundancy: int

@dataclass 
class Switch_DataClass: 
    id: str 
    ports: int
    domain: int

@dataclass 
class Link_DataClass: 
    id: str
    source: str
    destination: str
    sourcePort: int 
    destinationPort: int 
    domain: int 
    bandwidth_mbps: int
    delay: int

@dataclass
class EndSystem:
    id: str
    domain: int

@dataclass
class Topology:
    switches: List[Switch]
    end_systems: List[EndSystem]
    links: List[Link]
    default_bandwidth_mbps: float
    delay_units: str

@dataclass
class Path:
    node: str
    port: int


@dataclass
class Route:
    flow_id: int
    paths: List[List[Path]]
    min_e2e_delay_us: float    

def load_streams(path: str) -> Dict[int, Stream]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    streams = {}
    for s in raw["streams"]:
        destinations = [
            Destination(id=d["id"], deadline=d["deadline"])
            for d in s["destinations"]
        ]

        stream = Stream(
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


def load_routes(path: str) -> Dict[int, Route]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    routes = {}
    for r in raw["routes"]:
        parsed_paths = []
        for path_nodes in r["paths"]:
            hops = [Path(node=h["node"], port=h["port"]) for h in path_nodes]
            parsed_paths.append(hops)

        route = Route(
            flow_id=r["flow_id"],
            paths=parsed_paths,
            min_e2e_delay_us=r["min_e2e_delay"],
        )
        routes[route.flow_id] = route

    return routes


def load_topology(path: str) -> Topology:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)["topology"]

    switches = [Switch(**sw) for sw in raw["switches"]]
    end_systems = [EndSystem(**es) for es in raw["end_systems"]]

    links = [
        Link(
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

    return Topology(
        switches=switches,
        end_systems=end_systems,
        links=links,
        default_bandwidth_mbps=raw["default_bandwidth_mbps"],
        delay_units=raw["delay_units"],
    )
