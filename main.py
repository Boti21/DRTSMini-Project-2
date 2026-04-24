import parser
import func



if __name__ == "__main__":

    test_case = func.load_test_case("test_cases/test_case_1")

    func.validate_test_case(test_case)

    print(test_case)

    global_time = 0.0 # us


    pass