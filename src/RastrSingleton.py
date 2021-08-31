import win32com.client

# not thread-safed
class RastrMeta(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            instance = super().__call__(*args, **kwargs)
            cls.__instances[cls] = instance
        return cls.__instances[cls]


class RastrInstance(metaclass=RastrMeta):
    def __init__(self):
        self.__rastr = win32com.client.Dispatch('Astra.Rastr')

    def Load(self, file, template):
        return self.__rastr.Load(1, file, template)


