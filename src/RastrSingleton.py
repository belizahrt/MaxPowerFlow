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
    __outages: dict = {}
    __branchGroups: dict = {}

    def __init__(self):
        self.__rastr = win32com.client.Dispatch('Astra.Rastr')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')

    def ResetWorkspace(self):
        self.__rastr.NewFile('assets\\rastr_templates\\режим.rg2')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')
        self.__branchGroups.clear()

    def GetBranchGroups(self) -> dict:
        return self.__branchGroups

    def Load(self, file: str, template: str) -> str:
        try:
            self.__rastr.Load(1, file, template)
        except Exception as e:
            return e

        return None

    def RestorePFToggle(self):
        toggle = self.__rastr.GetToggle()
        if len(toggle.GetPositions()) > 0:
            toggle.MoveOnPosition(1)

    def SaveAll(self, file: str) -> str:
        try:
            self.__rastr.Save(file + '.rg2', 'assets\\rastr_templates\\режим.rg2')
            self.__rastr.Save(file + '.sch', 'assets\\rastr_templates\\сечения.sch')
            self.__rastr.Save(file + '.ut2', 'assets\\rastr_templates\\траектория утяжеления.ut2')
        except Exception as e:
            return e

        return None

    def MakeBranchGroup(self, bgNum, name) -> str:
        try:
            # make branchgroup in table sechen
            i = self.__rastr.Tables('sechen').size
            self.__rastr.Tables('sechen').AddRow()
            self.__rastr.Tables('sechen').Cols('ns').SetZ(i, bgNum)
            self.__rastr.Tables('sechen').Cols('name').SetZ(i, name)

            self.__branchGroups[bgNum] = i
        except Exception as e:
            return e

        return None

    def AddBranchToBranchGroup(self, bgNum, ip, iq) -> str:
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

    # PFVV - Power Flow Variance Vector
    def AddNodePFVV(self, nodeNum, recalcTan) -> [int, str]:
        i = -1
        try:
            # add vector in table ut_node
            i = self.__rastr.Tables('ut_node').size
            self.__rastr.Tables('ut_node').AddRow()
            self.__rastr.Tables('ut_node').Cols('ny').SetZ(i, nodeNum)
            self.__rastr.Tables('ut_node').Cols('tg').SetZ(i, recalcTan)
        except Exception as e:
            return -1, e

        return i, None

    def SetNodePFVVParam(self, id, param, value) -> str:
        try:
            self.__rastr.Tables('ut_node').Cols(param).SetZ(id, value)
        except Exception as e:
            return e

        return None

    def SetOutages(self, outages: dict):
        self.__outages = outages
        return None

    def GetBranchGroupPFValue(self, bgNum) -> float:
        try:
            return float(self.__rastr.Tables('sechen') \
                .Cols('psech').Z(self.__branchGroups[bgNum]))
        except:
            return None

    def CalcMaxPowerFlow(self, itersCount, 
            checkParameters=0x000, marginU=0.5) -> int:
        try:
            # setup pf options in table com_regim
            self.__rastr.Tables('com_regim').Cols('dv_min').SetZ(0, float(marginU))
            # setup utr options in table ut_common
            self.__rastr.Tables('ut_common').Cols('iter').SetZ(0, int(itersCount))

            self.__rastr.Tables('ut_common').Cols('enable_contr') \
                .SetZ(0, checkParameters != 0)
            self.__rastr.Tables('ut_common').Cols('dis_i_contr') \
                .SetZ(0, not (checkParameters & 0x001 == 0x001))
            self.__rastr.Tables('ut_common').Cols('dis_p_contr') \
                .SetZ(0, not (checkParameters & 0x010 == 0x010))
            self.__rastr.Tables('ut_common').Cols('dis_v_contr') \
                .SetZ(0, not (checkParameters & 0x100 == 0x100))

            # init utr & calc utr
            if self.__rastr.ut_utr('i') > 0:
                self.__rastr.ut_utr('')
            else:
                return -1
        except Exception as e:
            return -1

        return 0