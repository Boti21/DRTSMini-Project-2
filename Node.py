from CBSPort import *

class Node:
    ports = dict[int, TSNEgressPort]

    def __init__(self, name: str = "Unnamed", portsList: list = []):
        self.name = name
        self.portsList = portsList
        self.next = None

node = Node()