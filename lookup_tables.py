# from TSNStream import TSNStream
# from Node import Switch, EndDevice
# from Link import Link

nodes = []
streams =[]
links = []

# Accessort to lookupt tables
# def get_stream(stream_id: int) -> TSNStream:
#     for stream in streams:
#         if stream.stream_id == stream_id:
#             return stream
#     raise ValueError(f"Stream with id {stream_id} not found")
        
# def get_node(node_id: str) -> Switch | EndDevice:
#     for node in nodes:
#         if node.id == node_id:
#             return node
#     raise ValueError(f"Node with id {node_id} not found")

# def get_link(link_id: str) -> Link:
#     for link in links:
#         if link.id == link_id:
#             return link
#     raise ValueError(f"Link with id {link_id} not found")

def get_stream(stream_id: int):
    for stream in streams:
        if stream.stream_id == stream_id:
            return stream
    raise ValueError(f"Stream with id {stream_id} not found")
        
def get_node(node_id: str):
    for node in nodes:
        if node.id == node_id:
            return node
    raise ValueError(f"Node with id {node_id} not found")

def get_link(link_id: str):
    for link in links:
        if link.id == link_id:
            return link
    raise ValueError(f"Link with id {link_id} not found")