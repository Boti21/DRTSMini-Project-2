from parser import StreamDataclass


class TSNStream:
    """Represents a single stream in the network."""

    def __init__(self, stream: StreamDataclass):
        self.stream_id = stream.id
        self.name = stream.name
        self.source = stream.source
        self.destinations = stream.destinations
        self.type = stream.stream_type
        self.pcp = stream.pcp
        self.size_bytes = stream.size
        self.period = stream.period  # Units specified by "delay_units" in streams.json
        self.redundancy = (
            stream.redundancy
        )  # Number of redundant copies (for reliability)
        self.arrival_time = 0  # Time reached current switch
        self.hop_index = 0  # Track progress along route

    def step(self, global_time: float):
        if global_time % self.period == 0:
            frame = TSNFrame(self, global_time)
        ######
        ##### ADD LOOKUP TABLE LOGIC
        ######

    def __repr__(self):
        return f"Frame Stream:{self.stream_id} PCP:{self.pcp} Size:{self.size_bytes}B"


class TSNFrame:
    """Represents a single message instance (packet) in the network."""

    def __init__(self, stream: StreamDataclass, arrival_time: float):
        self.stream_id = stream.id
        self.name = stream.name
        self.source = stream.source
        self.destinations = stream.destinations
        self.type = stream.stream_type
        self.pcp = stream.pcp
        self.size_bytes = stream.size
        self.redundancy = (
            stream.redundancy
        )  # Number of redundant copies (for reliability)
        self.arrival_time = arrival_time  # Time reached current switch
        self.hop_index = 0  # Track progress along route

    def __repr__(self):
        return f"Frame Stream:{self.stream_id} PCP:{self.pcp} Size:{self.size_bytes}B"
