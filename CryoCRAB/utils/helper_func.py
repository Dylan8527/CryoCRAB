from time import perf_counter

def timer(func):
    """
    Timer decorator, used to calculate the time cost of a function.
    
    Args:
        func (function): The function to be calculated.
    """
    def func_wrapper(*args, **kwargs):
        func_st = perf_counter()
        return_value = func(*args, **kwargs)
        func_ed = perf_counter()
        return return_value, func_st, func_ed
    return func_wrapper