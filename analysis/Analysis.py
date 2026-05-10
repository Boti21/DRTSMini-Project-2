"""
    This analyzer calculates the worst-case response time of a stream.
    The WCRT depends on the topology and the load within the system.
"""

"""
    FLOW = STREAM (kill me]
"""

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
                serialization_delay = stream.size_bytes*8 / port.bandwidth_bps * 1e6
                # propagation_delay = port.link.delay
                propagation_delay = 0 # "Academic papers usually assume no propgation delay"

                spi = self.__spi_calc__(port, stream, node.node)
                hpi = self.__hpi_calc__(port, stream, node.node)
                lpi = self.__lpi_calc__(port, stream, node.node)
                print(f"spi = {spi:.2f}     hpi = {hpi:.2f}     lpi = {lpi:.2f}")
                wcrt += spi + hpi + lpi + propagation_delay + serialization_delay
        return wcrt

    def __spi_calc__(self, port: TSNEgressPort, stream: TSNStream, node: str): # Same priority interference
        queue = None
        if stream.pcp == 2:
            queue = port.queues["A"]
        elif stream.pcp == 1:
            queue = port.queues["B"]
        else:
            queue = port.queues["BE"]

        if queue.idle_slope == 0: # Avoid division by zero
            return 0

        streams_on_port = self.__get_streams_on_port__(port=port, node=node)

        spi = 0
        for s in streams_on_port:
            if s.stream_id == stream.stream_id: continue
            if s.pcp != stream.pcp: continue
            frame_tx_time = s.size_bytes*8 / port.bandwidth_bps * 1e6 # Only one frame per stream so max frame size = frame size
            spi += frame_tx_time * (1 + abs(queue.send_slope) / queue.idle_slope)

        return spi

    def __hpi_calc__(self, port: TSNEgressPort, stream: TSNStream, node: str): # Higher priority interference
        if stream.pcp == 1: # AVB class B
            queue = port.queues["A"]
            L_max = self.__max_transmission_time__(port=port, node=node, ignore_id=stream.stream_id, pcp=2)
            credit_recovery = (abs(queue.idle_slope / queue.send_slope)) * self.__lpi_calc__(port=port, stream=stream, node=node)
            return credit_recovery + L_max
        if stream.pcp == 0:
            queue = port.queues["B"]
            L_max = self.__max_transmission_time__(port=port, node=node, ignore_id=stream.stream_id, pcp=1)
            credit_recovery = (abs(queue.idle_slope / queue.send_slope)) * self.__lpi_calc__(port=port, stream=stream, node=node)
            hpi = credit_recovery + L_max
            queue = port.queues["A"]
            L_max = self.__max_transmission_time__(port=port, node=node, ignore_id=stream.stream_id, pcp=2)
            credit_recovery = (abs(queue.idle_slope / queue.send_slope)) * self.__lpi_calc__(port=port, stream=stream, node=node)
            return hpi + credit_recovery + L_max
        return 0

    def __lpi_calc__(self, port: TSNEgressPort, stream: TSNStream, node: str): # Lower priority interference
        if stream.pcp == 2: # AVB class A
            return self.__max_transmission_time__(port=port, node=node, ignore_id=stream.stream_id)
        if stream.pcp == 1: # AVB class B
            return self.__max_transmission_time__(port=port, node=node, ignore_id=stream.stream_id, pcp=0)
        return 0 # If PCP is 0 then there's no lower priority interference

    def __max_transmission_time__(self, port: TSNEgressPort, node: str, ignore_id: int, pcp: int=None):
        max = 0
        streams_on_port = self.__get_streams_on_port__(port=port, node=node)

        for s in streams_on_port:
            if s.stream_id == ignore_id: continue
            if pcp is not None and s.pcp != pcp: continue
            val = s.size_bytes*8/port.bandwidth_bps * 1e6 # μs
            if val > max: max = val
        return max

    def __get_streams_on_port__(self, port: TSNEgressPort, node: str):
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
