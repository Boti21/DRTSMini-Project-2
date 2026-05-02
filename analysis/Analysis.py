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

class Analyzer:
    def __init__(self, route: list[Node], stream: TSNStream):
        self.wcrt = 0
        return self.wcrt_cal(route=route, stream=stream)

    def wcrt_cal(self, route: list[Node], stream: TSNStream):
        for node in route:
            for _, port in node.ports.items():
                if port.port_id == 0: # Only receiving
                    continue
                self.wcrt += self.spi_calc(port, stream) + \
                             self.hpi_calc(port, stream) + \
                             self.lpi_calc(port, stream) + \
                             port.link.delay # göh?
        return self.wcrt

    def spi_calc(self, port: TSNEgressPort, stream: TSNStream): # Same priority interference
        queue = Node
        spi = 0
        if stream.pcp == 1:
            queue = port.queues["A"]
        elif stream.pcp == 2:
            queue = port.queues["B"]
        else:
            queue = port.queues["BE"]

        for frame in queue.buffer:
            if frame.stream_id == stream.stream_id: continue
            spi += port.link.delay*frame.size/port.link.bandwidth_mbps * (1 + queue.send_slope/queue.idle_slope)

        return spi

        # return (len(queue.buffer)-1) * port.link.delay * (len(queue)-1) * (1 + queue.send_slope/queue.idle_slope) # len(queue)-1 because the frame itself is not counted


    def hpi_calc(self, port: TSNEgressPort, stream: TSNStream): # Higher priority interference
        # if stream.pcp == 1: # AVB class A
        #     return 0
        if stream.pcp == 2: # AVB class B
            # return self.lpi_calc(port=port, stream=stream) * port.idle_slope/port.send_slope + port.link.delay*(len(port.queues["A"]) - 1)
            queue = port.queues["A"]
            return self.lpi_calc(port=port, stream=stream) * queue.idle_slope/queue.send_slope + self.max_transmission_time(port=port, queue=queue, ignore_id=stream.stream_id)
        return 0 # Best Effort queue not taken into account

    def lpi_calc(self, port, stream): # Lower priority interference
        if stream.pcp == 1:
            queue = port.queues["B"]
            return self.max_transmission_time(port=port, queue=queue, ignore_id=stream.stream_id)
        return 0 # Best Effort queue not taken into account

    def max_transmission_time(self, port: TSNEgressPort, queue: CBSQueue, ignore_id: int):
        max = 0
        for frame in queue.buffer:
            if frame.stream_id == ignore_id: continue
            val = port.link.delay*frame.size/port.link.bandwidth_mbps
            if val > max: max = val
        return max
