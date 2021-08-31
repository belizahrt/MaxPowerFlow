import win32com.client
import sys

# not thread-safed
class RastrMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class RastrInstance(metaclass=RastrMeta):
    def __init__(self):
        self.rastr = win32com.client.Dispatch('Astra.Rastr')

    def __some_business_logic(self):
        print("bl")


rastrInstance = RastrInstance()

