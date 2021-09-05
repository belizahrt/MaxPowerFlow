# calc engine for MaxPowerFlow

import win32com.client
from typing import Optional


# not thread-safe
class RastrMeta(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            instance = super().__call__(*args, **kwargs)
            cls.__instances[cls] = instance
        return cls.__instances[cls]


class RastrInstance(metaclass=RastrMeta):
    __branch_groups: dict = {}

    def __init__(self):
        self.__rastr = win32com.client.Dispatch('Astra.Rastr')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')

    def reset_workspace(self):
        """

        """
        self.__rastr.NewFile('assets\\rastr_templates\\режим.rg2')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')
        self.__branch_groups.clear()

    def get_branch_groups(self) -> dict:
        """

        :return:
        """
        return self.__branch_groups

    def load(self, file: str, template: str) -> Optional[str]:
        """

        :param file:
        :param template:
        :return:
        """
        try:
            self.__rastr.load(1, file, template)
        except Exception as e:
            return e

        return None

    def restore_pf_toggle(self, position: int = 1) -> None:
        """

        :param position:
        """
        toggle = self.__rastr.GetToggle()
        if len(toggle.GetPositions()) >= position:
            toggle.MoveOnPosition(position)

    def get_toggle_positions_count(self) -> int:
        """

        :return:
        """
        toggle = self.__rastr.GetToggle()
        return len(toggle.GetPositions())

    # tests
    def save_all(self, file: str) -> Optional[str]:
        try:
            self.__rastr.Save(file + '.rg2', 'assets\\rastr_templates\\режим.rg2')
            self.__rastr.Save(file + '.sch', 'assets\\rastr_templates\\сечения.sch')
            self.__rastr.Save(file + '.ut2', 'assets\\rastr_templates\\траектория утяжеления.ut2')
        except Exception as e:
            return e

        return None

    def make_branch_group(self, bg_num: int, name: str) -> Optional[str]:
        """

        :param bg_num:
        :param name:
        :return:
        """
        try:
            # make branchgroup in table sechen
            i = self.__rastr.Tables('sechen').size
            self.__rastr.Tables('sechen').AddRow()
            self.__rastr.Tables('sechen').Cols('ns').SetZ(i, bg_num)
            self.__rastr.Tables('sechen').Cols('name').SetZ(i, name)

            self.__branch_groups[bg_num] = i
        except Exception as e:
            return e

        return None

    def add_branch_to_branch_group(self, bg_num: int,
                                   ip: int, iq: int) -> Optional[str]:
        """

        :param bg_num:
        :param ip:
        :param iq:
        :return:
        """
        try:
            # add lines for branchgroup in table grline
            i = self.__rastr.Tables('grline').size
            self.__rastr.Tables('grline').AddRow()
            self.__rastr.Tables('grline').Cols('ns').SetZ(i, bg_num)
            self.__rastr.Tables('grline').Cols('ip').SetZ(i, ip)
            self.__rastr.Tables('grline').Cols('iq').SetZ(i, iq)
        except Exception as e:
            return e

        return None

    # PFVV - Power Flow Variance Vector
    def add_node_pfvv(self, node_num: int, recalc_tan: int) -> [int, str]:
        """

        :param node_num:
        :param recalc_tan:
        :return:
        """
        i = -1
        try:
            # add vector in table ut_node
            i = self.__rastr.Tables('ut_node').size
            self.__rastr.Tables('ut_node').AddRow()
            self.__rastr.Tables('ut_node').Cols('ny').SetZ(i, node_num)
            self.__rastr.Tables('ut_node').Cols('tg').SetZ(i, recalc_tan)
        except Exception as e:
            return -1, e

        return i, None

    def set_node_pfvv_param(self, node_id: int,
                            param: str, value: any) -> Optional[str]:
        """

        :param node_id:
        :param param:
        :param value:
        :return:
        """
        try:
            self.__rastr.Tables('ut_node').Cols(param).SetZ(node_id, value)
        except Exception as e:
            return e

        return None

    def get_branch_group_pf_value(self, bg_num: int) -> Optional[float]:
        """

        :param bg_num:
        :return:
        """
        try:
            return float(self.__rastr.Tables('sechen') \
                         .Cols('psech').Z(self.__branch_groups[bg_num]))
        except:
            return None

    def power_flow(self, param: str = '') -> Optional[int]:
        """

        :param param:
        :return:
        """
        try:
            return int(self.__rastr.rgm(param))
        except:
            return None

    def calc_max_power_flow(self, iters_count: int = 100,
                            check_parameters: int = 0x000,
                            margin_u: float = 0.5) -> int:
        """

        :param iters_count:
        :param check_parameters:
        :param margin_u:
        :return:
        """
        try:
            # setup pf options in table com_regim
            self.__rastr.Tables('com_regim').Cols('dv_min').SetZ(0, float(margin_u))
            # setup utr options in table ut_common
            self.__rastr.Tables('ut_common').Cols('iter').SetZ(0, int(iters_count))

            self.__rastr.Tables('ut_common').Cols('enable_contr') \
                .SetZ(0, check_parameters != 0)
            self.__rastr.Tables('ut_common').Cols('dis_i_contr') \
                .SetZ(0, not (check_parameters & 0x001 == 0x001))
            self.__rastr.Tables('ut_common').Cols('dis_p_contr') \
                .SetZ(0, not (check_parameters & 0x010 == 0x010))
            self.__rastr.Tables('ut_common').Cols('dis_v_contr') \
                .SetZ(0, not (check_parameters & 0x100 == 0x100))

            # init utr & calc utr
            if self.__rastr.ut_utr('i') > 0:
                self.__rastr.ut_utr('')
            else:
                return -1

        except Exception as e:
            return -1

        return 0

    def change_branch_state(self, ip: int, iq: int, np: int, state: str) -> int:
        """

        :param ip:
        :param iq:
        :param np:
        :param state:
        :return:
        """
        try:
            vetv = self.__rastr.Tables('vetv')
            vetv.SetSel('ip={_ip}&iq={_iq}&np={_np}'.format(_ip=ip, _iq=iq, _np=np))
            vetv.Cols('sta').Calc(state)
        except:
            return -1
        return 0

    # swap normal and emergency current limits, cause
    # rastr can only consider normal current limits
    def swap_current_limits(self) -> int:
        """

        :return:
        """
        try:
            for i in range(0, self.__rastr.Tables('vetv').size):
                normal_i = self.__rastr.Tables('vetv').cols('i_dop').Z(i)
                emergency_i = self.__rastr.Tables('vetv').cols('i_dop_av').Z(i)

                self.__rastr.Tables('vetv').cols('i_dop').SetZ(i, emergency_i)
                self.__rastr.Tables('vetv').cols('i_dop_av').SetZ(i, normal_i)
        except:
            return -1
        return 0
