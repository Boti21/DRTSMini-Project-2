"""
    This analyzer calculates the worst-case response time of a stream.
    The WCRT depends on the topology and the load within the system.
"""

"""
    FLOW = STREAM (kill me]
"""

from numpy import double
from CBSPort import *
from TSNStream import *
from Node import *
from Link import *
from parser import *
from lookup_tables import *

class Analyzer:
    def __init__(self):
        self.wcrts = {}

    def analyze_all(self, routes: dict[int, RouteDataclass], streams: list[TSNStream]):
        self.streams = streams
        self.routes = routes
        for stream in streams:
            self.wcrts[stream.stream_id] = self.wcrt_cal(route=routes[stream.stream_id], stream=stream)

    def wcrt_cal(self, route: RouteDataclass, stream: TSNStream):
        wcrt = 0
        for path in route.paths: # We only have one path for now
            for node in path:
                if node == path[-1]: continue

                actual_node = get_node(node.node)
                port = actual_node.ports[node.port]
                serialization_delay = stream.size_bytes*8 / (port.link.bandwidth_mbps * 1e6) * 1e6
                propagation_delay = port.link.delay

                spi = self.spi_calc(port, stream, node.node)
                hpi = self.hpi_calc(port, stream, node.node)
                lpi = self.lpi_calc(port, stream, node.node)
                print(f"Same priority interference: {spi}")
                print(f"Higher priority interference: {hpi}")
                print(f"Lower priority interference: {lpi}")
                wcrt += spi + hpi + lpi + propagation_delay + serialization_delay
                # wcrt += self.spi_calc(port, stream, node.node) + \
                #         self.hpi_calc(port, stream, node.node) + \
                #         self.lpi_calc(port, stream, node.node) + \
                #         propagation_delay + \
                #         serialization_delay
        return wcrt

    def spi_calc(self, port: TSNEgressPort, stream: TSNStream, node: str): # Same priority interference
        queue = None
        spi = 0
        if stream.pcp == 1:
            queue = port.queues["A"]
        elif stream.pcp == 2:
            queue = port.queues["B"]
        else:
            return 0
            # queue = port.queues["BE"]

        if queue.idle_slope == 0: # Avoid division by zero
            return 0

        streams_on_port = self._get_streams_on_port(port=port, node=node)

        for s in streams_on_port:
            if s.stream_id == stream.stream_id: continue
            if s.pcp != stream.pcp: continue
            frame_tx_time = s.size_bytes*8 / (port.link.bandwidth_mbps*1e6) * 1e6 # Only one frame per stream so max frame size = frame size
            spi += frame_tx_time * (1 + abs(queue.send_slope) / queue.idle_slope)

        # for frame in queue.buffer:
        #     if frame.stream_id == stream.stream_id: continue
        #     spi += frame.size_bytes*8/port.link.bandwidth_mbps * (1 + abs(queue.send_slope)/queue.idle_slope)

        return spi

    def hpi_calc(self, port: TSNEgressPort, stream: TSNStream, node: str): # Higher priority interference
        if stream.pcp == 1: # AVB class B
            queue = port.queues["A"]
            L_max = self.max_transmission_time(port=port, node=node, ignore_id=stream.stream_id)
            credit_recovery = (abs(queue.send_slope) / queue.idle_slope) * L_max
            return credit_recovery + L_max

        # elif stream.pcp == 0: # BE
        #     hpi = 0
        #     for key in ["A", "B"]:
        #         queue = port.queues[key]
        #         L_max = self.max_transmission_time(port=port, node=node, ignore_id=stream.stream_id)
        #         credit_recovery = (abs(queue.send_slope) / queue.idle_slope) * L_max
        #         hpi += credit_recovery + L_max
        #     return hpi
        return 0 # If PCP is 2 then there's no higher priority interference

    def lpi_calc(self, port: TSNEgressPort, stream: TSNStream, node: str): # Lower priority interference
        if stream.pcp == 2: # AVB class A
            return (self.max_transmission_time(port=port, node=node, ignore_id=stream.stream_id, pcp=1))
                    # self.max_transmission_time(port=port, node=node, ignore_id=stream.stream_id, pcp=0))
        # elif stream.pcp == 1: # AVB class B
        #     return self.max_transmission_time(port=port, node=node, ignore_id=stream.stream_id)
        return 0 # If PCP is 0 then there's no lower priority interference

    def max_transmission_time(self, port: TSNEgressPort, node: str, ignore_id: int, pcp: int=None):
        max = 0
        streams_on_port = self._get_streams_on_port(port=port, node=node)

        for s in streams_on_port:
            if s.stream_id == ignore_id: continue
            if pcp is not None and s.pcp != pcp: continue
            val = s.size_bytes*8/(port.link.bandwidth_mbps*1e6) * 1e6 # μs
            if val > max: max = val
        return max

    def _get_streams_on_port(self, port: TSNEgressPort, node: str):
        streams_on_port = []
        for s in self.streams:
            route = self.routes[s.stream_id]
            for path in route.paths:
                last_hop = path[-1]
                for n in path:
                    if n == last_hop: continue # Skip destination receive port
                    if n.node == node and n.port == port.port_id:
                        streams_on_port.append(s)
        return streams_on_port
