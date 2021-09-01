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

    def Load(self, file: str, template: str):
        return self.__rastr.Load(1, file, template)

    def MakeBranchGroup(self, branches):
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')

        bgNum = 1
        # make branchgroup in table sechen
        self.__rastr.Tables('sechen').AddRow()
        self.__rastr.Tables('sechen').Cols('ns').SetZ(0, bgNum)
        self.__rastr.Tables('sechen').Cols('name').SetZ(0, 'MaxPFBranchGroup')

        # add lines for branchgroup in table grline
        i = 0
        for branch in branches:
            self.__rastr.Tables('grline').AddRow()
            self.__rastr.Tables('grline').Cols('ns').SetZ(i, bgNum)
            self.__rastr.Tables('grline').Cols('ip').SetZ(i, branches[branch].get('ip', 0))
            self.__rastr.Tables('grline').Cols('iq').SetZ(i, branches[branch].get('iq', 0))
            i += 1

        # test save
        self.__rastr.Save('asd.sch', 'assets\\rastr_templates\\сечения.sch')
