# calc engine for MaxPowerFlow

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
    __outages: dict = None
    __bgNum: int = 0

    def __init__(self):
        self.__rastr = win32com.client.Dispatch('Astra.Rastr')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')

    def ResetWorkspace(self):
        self.__rastr.NewFile('assets\\rastr_templates\\режим.rg2')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')
        __bgNum = 0

    def GetBranchGroupNum(self):
        return self.__bgNum

    def Load(self, file: str, template: str):
        try:
            self.__rastr.Load(1, file, template)
        except Exception as e:
            return e

        return None

    def SaveAll(self, file: str):
        try:
            self.__rastr.Save(file + '.rg2', 'assets\\rastr_templates\\режим.rg2')
            self.__rastr.Save(file + '.sch', 'assets\\rastr_templates\\сечения.sch')
            self.__rastr.Save(file + '.ut2', 'assets\\rastr_templates\\траектория утяжеления.ut2')
        except Exception as e:
            return e

        return None

    def MakeBranchGroup(self, name):
        try:
            # make branchgroup in table sechen
            self.__rastr.Tables('sechen').AddRow()
            self.__bgNum += 1
            self.__rastr.Tables('sechen').Cols('ns').SetZ(0, self.__bgNum)
            self.__rastr.Tables('sechen').Cols('name').SetZ(0, name)
        except Exception as e:
            return e

        return None

    def AddBranchToBranchGroup(self, bgNum, ip, iq):
        try:
            # add lines for branchgroup in table grline
            i = self.__rastr.Tables('grline').size
            self.__rastr.Tables('grline').AddRow()
            self.__rastr.Tables('grline').Cols('ns').SetZ(i, bgNum)
            self.__rastr.Tables('grline').Cols('ip').SetZ(i, ip)
            self.__rastr.Tables('grline').Cols('iq').SetZ(i, iq)
        except Exception as e:
            return e

        return None

    def SetOutages(self, outages: dict):
        self.__outages = outages
        return None