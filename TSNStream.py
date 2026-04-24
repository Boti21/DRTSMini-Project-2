from parser import StreamDataClass


class TSNStream:
    """Represents a single stream in the network."""

    def __init__(self, stream: StreamDataClass):
        self.stream_id = stream.stream_id
        self.name = stream.name
        self.source = stream.source
        self.destinations = stream.destinations
        self.type = stream.type
        self.pcp = stream.pcp
        self.size_bytes = stream.size_bytes
        self.period = stream.period  # Units specified by "delay_units" in streams.json
        self.redundancy = (
            stream.redundancy
        )  # Number of redundant copies (for reliability)
        self.arrival_time = 0  # Time reached current switch
        self.hop_index = 0  # Track progress along route

    def step(self, global_time: float):
        frame = TSNFrame(self, global_time)
        ######
        ##### ADD LOOKUP TABLE LOGIC
        ######

    def __repr__(self):
        return f"Frame Stream:{self.stream_id} PCP:{self.pcp} Size:{self.size_bytes}B"


class TSNFrame:
    """Represents a single message instance (packet) in the network."""

    def __init__(self, stream: StreamDataClass, arrival_time: float):
        self.stream_id = stream.stream_id
        self.name = stream.name
        self.source = stream.source
        self.destinations = stream.destinations
        self.type = stream.type
        self.pcp = stream.pcp
        self.size_bytes = stream.size_bytes
        self.redundancy = (
            stream.redundancy
        )  # Number of redundant copies (for reliability)
        self.arrival_time = arrival_time  # Time reached current switch
        self.hop_index = 0  # Track progress along route

    def __repr__(self):
        return f"Frame Stream:{self.stream_id} PCP:{self.pcp} Size:{self.size_bytes}B"
