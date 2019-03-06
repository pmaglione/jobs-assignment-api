from src.helpers import mv_single_binary, truth_finder_single


class AggregationFunctionFactory:
    @staticmethod
    def get_function(fn_name):
        if fn_name == "MV":
            return mv_single_binary
        elif fn_name == "EM":
            return truth_finder_single
        else:
            return mv_single_binary
