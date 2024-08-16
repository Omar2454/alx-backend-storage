#!/usr/bin/env python3

from typing import Callable, Optional, Union
from uuid import uuid4
import redis
from functools import wraps

'''
    Writing strings to Redis.
'''


def count_calls(method: Callable) -> Callable:
    '''
        Counts the number of times a method is called.
    '''

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        '''
            Wrapper function.
        '''
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """ Decorator to store the history of inputs and
    outputs for a particular function.
    """
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"

    @wraps(method)
    def wrapper(self, *args, **kwargs):  # sourcery skip: avoid-builtin-shadow
        """ Wrapper for decorator functionality """
        self._redis.rpush(inputs, str(args))
        data = method(self, *args, **kwargs)
        self._redis.rpush(outputs, str(data))
        return data

    return wrapper


import redis
from typing import Callable

def replay(method: Callable) -> None:
    """
    Replays the history of a function by retrieving and displaying the 
    stored inputs and outputs from Redis.

    Args:
        method (Callable): The function whose call history you want to replay.

    Returns:
        None: The function prints the call history, including the number of times
              the method was called, the inputs passed, and the outputs returned.
    """
    # Get the fully qualified name of the method (e.g., 'Cache.store')
    name = method.__qualname__

    # Create a Redis client to interact with the Redis server
    cache = redis.Redis()

    # Retrieve the number of times the method was called from Redis
    # Decode the result from bytes to a UTF-8 string
    calls = cache.get(name).decode("utf-8")

    # Print the number of calls made to the method
    print("{} was called {} times:".format(name, calls))

    # Retrieve the list of inputs and outputs from Redis
    # `lrange` retrieves all elements of the list stored at the specified key
    inputs = cache.lrange(name + ":inputs", 0, -1)
    outputs = cache.lrange(name + ":outputs", 0, -1)

    # Iterate over the paired inputs and outputs using zip
    for i, o in zip(inputs, outputs):
        # Decode both the input and output from bytes to UTF-8 strings
        decoded_input = i.decode('utf-8')
        decoded_output = o.decode('utf-8')

        # Print the method name, input arguments, and output in the specified format
        print("{}(*{}) -> {}".format(name, decoded_input, decoded_output))



class Cache:
    '''
        Cache class.
    '''
    def __init__(self):
        '''
            Initialize the cache.
        '''
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        '''
            Store data in the cache.
        '''
        randomKey = str(uuid4())
        self._redis.set(randomKey, data)
        return randomKey

    def get(self, key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        '''
            Get data from the cache.
        '''
        value = self._redis.get(key)
        if fn:
            value = fn(value)
        return value

    def get_str(self, key: str) -> str:
        '''
            Get a string from the cache.
        '''
        value = self._redis.get(key)
        return value.decode('utf-8')

    def get_int(self, key: str) -> int:
        '''
            Get an int from the cache.
        '''
        value = self._redis.get(key)
        try:
            value = int(value.decode('utf-8'))
        except Exception:
            value = 0
        return value
