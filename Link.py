from parser import LinkDataClass
from TSNStream import TSNFrame


class Link:
    receiving_queue = list[tuple[TSNFrame, float]]  # Queue of (frame, arrival_time)
    current_time: float = 0.0

    def __init__(self, link_data: LinkDataClass):
        self.id = link_data.id
        self.source = link_data.source
        self.destination = link_data.destination
        self.source_port = link_data.sourcePort
        self.destination_port = link_data.destinationPort
        self.domain = link_data.domain
        self.bandwidth_mbps = link_data.bandwidth_mbps
        self.delay = link_data.delay

    def receive_frame(self, frame: TSNFrame):
        self.receiving_queue.append((frame, self.current_time))

    def step(self, global_time: float):
        # Check if any frames have completed their transmission delay
        self.current_time = global_time
        for frame, arrival_time in self.receiving_queue:
            if self.current_time - arrival_time >= self.delay:
                # Frame has reached the destination
                ##########
                ##### ADD LOGIC FOR LOOKUP TABLE
                ###########
                print(f"Link {self.id} delivered frame: {frame} at time {global_time}")
                self.receiving_queue.remove((frame, arrival_time))
