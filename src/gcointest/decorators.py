
import time

from gcointest.exceptions import CoreException, BitcoinException


def severaltry(time_out=300, sleep_interval=1):
    def decorator(fun):
        def func_wrapper(*args, **kwargs):
            loop_cnt = (time_out/sleep_interval) + 1
            while loop_cnt > 0:
                try:
                    return fun(*args, **kwargs)
                except (CoreException, BitcoinException):
                    pass
                time.sleep(sleep_interval)
                loop_cnt -= 1
        return func_wrapper
    return decorator

