import parser
import func
from Node import Switch, EndDevice



if __name__ == "__main__":

    test_case = func.load_test_case("test_cases/test_case_1")

    func.validate_test_case(test_case)

    print(test_case)

    MAX_SIMULATION_TIME_US = 1_000_000.0 # 1 second in microseconds
    global_time = 0.0 # us

    # List to make them iterable
    nodes = []
    for node in test_case.topology.switches:
        nodes.append(Switch(id=node.id, domain=node.domain, ports=node.ports))
    for node in test_case.topology.end_systems:
        nodes.append(EndDevice(id=node.id, domain=node.domain))




    streams = []

    for stream_id, stream in test_case.streams.items():
        print(f"Stream {stream_id}: {stream}")
        # instantiate the sream objects

    links = []







    while global_time < MAX_SIMULATION_TIME_US:






        global_time += 1 # Advance by 1 us
        pass


    pass