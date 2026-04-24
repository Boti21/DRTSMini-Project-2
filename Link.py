from parser import Link_DataClass
from CBSPort import TSNFrame


class Link:
    def __init__(self, link_data: Link_DataClass):
        self.id = link_data.id
        self.source = link_data.source
        self.destination = link_data.destination
        self.source_port = link_data.sourcePort
        self.destination_port = link_data.destinationPort
        self.domain = link_data.domain
        self.bandwidth_mbps = link_data.bandwidth_mbps
        self.delay = link_data.delay

    def receive_frame(self, frame: TSNFrame):
        
