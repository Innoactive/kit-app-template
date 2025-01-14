from datetime import datetime, timedelta
from functools import wraps


def throttle(seconds=0, minutes=0, hours=0, skip_condition=None):
    """
    Decorator that throttles function calls, unless skip_condition(*args, **kwargs) is True.

    :param seconds: Number of seconds in the throttle window
    :param minutes: Number of minutes in the throttle window
    :param hours:   Number of hours in the throttle window
    :param skip_condition: A callable receiving (*args, **kwargs). If it returns True,
                           we skip throttling and call the function immediately.
    """
    throttle_period = timedelta(seconds=seconds, minutes=minutes, hours=hours)

    # If no skip_condition is provided, define a default function that always returns False
    if skip_condition is None:

        def default_skip_condition(*args, **kwargs):
            return False

        skip_condition = default_skip_condition

    def throttle_decorator(fn):
        time_of_last_call = datetime.min

        @wraps(fn)
        def wrapper(*args, **kwargs):
            nonlocal time_of_last_call  # Moved to beginning of function

            # If skip_condition is met, call fn immediately and don't throttle
            if skip_condition(*args, **kwargs):
                return fn(*args, **kwargs)

            now = datetime.now()
            # If enough time has passed since the last call, or it's the first call, run the function
            if now - time_of_last_call > throttle_period:
                time_of_last_call = now
                return fn(*args, **kwargs)
            # Otherwise, do nothing (or return None, or raise an exception, depending on your needs)

        return wrapper

    return throttle_decorator
