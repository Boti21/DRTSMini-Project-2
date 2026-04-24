from parser import LinkDataclass, StreamDataclass
from TSNStream import TSNFrame


class Link:
    current_time: float = 0.0

    def __init__(self, link_data: LinkDataclass):
        self.id = link_data.id
        self.source = link_data.source
        self.destination = link_data.destination
        self.source_port = link_data.sourcePort
        self.destination_port = link_data.destinationPort
        self.domain = link_data.domain
        self.bandwidth_mbps = link_data.bandwidth_mbps
        self.delay = link_data.delay
        self.receiving_queue = list[tuple[TSNFrame, float]]()

    def receive_frame(self, frame: TSNFrame):
        print(f"Link {self.id} received frame: {frame} at time {self.current_time}")
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


if __name__ == "__main__":
    # Example usage
    link_data = LinkDataclass(
        id="link1",
        source="switch1",
        destination="switch2",
        sourcePort=1,
        destinationPort=1,
        domain=0,
        bandwidth_mbps=100,
        delay=10,
    )
    link = Link(link_data)
    stream_data = StreamDataclass(
        id="stream1",
        name="Test Stream",
        source="switch1",
        destinations=[],
        stream_type="TypeA",
        pcp=0,
        size=1000,
        period=100,
        redundancy=0,
    )
    frame = TSNFrame(
        stream=stream_data,  # This would be a StreamDataclass instance in a real scenario
        arrival_time=0,
    )
    link.receive_frame(frame)
    link.step(1)
