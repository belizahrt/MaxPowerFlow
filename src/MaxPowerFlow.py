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
        self.__rastr = win32com.client.Dispatch('Astra.Rastr')

    def Load(self, file, template):
        try:
            self.__rastr.Load(1, file, template)
        except:
            return -1
        return 0


def ReadCmdLine(argv):
    params = {}

    for i in range(1, len(argv)):
        if i == len(argv)-1:
            break

        params[argv[i]] = argv[i+1]
        i += 1
    
    return params

def DoInitializeData(argv):
    
    params = ReadCmdLine(argv)
          
    if '-rg2' in params and '-rg2template' in params:
        if RastrInstance().Load(params['-rg2'], params['-rg2template']) == -1:
            print('Incorrect IRastr launch params (rg2, template)')
            return -1
    else:
        print('No rg2 files paths in cmd args')
        return -1



    return 0


print(DoInitializeData(sys.argv))