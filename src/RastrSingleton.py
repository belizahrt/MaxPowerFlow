# calc engine for MaxPowerFlow

import win32com.client
from typing import Optional


# not thread-safe singleton
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

    def reset_workspace(self) -> None:
        """
        clear all tables in rg2, sch, ut2 templates files
        """
        self.__rastr.NewFile('assets\\rastr_templates\\режим.rg2')
        self.__rastr.NewFile('assets\\rastr_templates\\сечения.sch')
        self.__rastr.NewFile('assets\\rastr_templates\\траектория утяжеления.ut2')
        self.__branch_groups.clear()

    def get_branch_groups(self) -> dict:
        """
        get map of branch groups in format {num of bg: id of bg in 'sechen' table}
        :return: private object
        """
        return self.__branch_groups

    def load(self, file: str, template: str) -> Optional[str]:
        """
        load file by path with template and replace corresponding opened file in workspace
        :param file: file path
        :param template: template path
        :return: None - file was load successfully or COM Exception string
        """
        try:
            self.__rastr.load(1, file, template)
        except Exception as e:
            return e

        return None

    def restore_pf_toggle(self, position: int = 1) -> None:
        """
        get rastr PF toggle (to switch beetween calculating steps)
        :param position: number of calculating step (from 1 to get_toggle_positions_count)
            position = 1 is origin PF
        """
        toggle = self.__rastr.GetToggle()
        if len(toggle.GetPositions()) >= position:
            toggle.MoveOnPosition(position)

    def get_toggle_positions_count(self) -> int:
        """
        :return: calculating steps count
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
        create new branch group in table 'sechen'
        :param bg_num: number of branch group (semantic number)
        :param name: name of branch group
        :return: None - file was load successfully or COM Exception string
        """
        try:
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
        add branch with ip and iq node endings in branch group
        :param bg_num: number of branch group
        :param ip: begin node
        :param iq: end node
        :return: None - file was load successfully or COM Exception string
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

    def add_node_pfvv(self, node_num: int, recalc_tan: int) -> [int, str]:
        """
        add node to 'ut_node' table (new component of pfvv)
        :param node_num: number of node
        :param recalc_tan: 0 - no power recalc consider power coeff (tan), 
            1 - recalc power consider tan
        :return: tuple <new id in table (-1 if adding failed), None (COM exception text if failed)>
        """
        i = -1
        try:
            i = self.__rastr.Tables('ut_node').size
            self.__rastr.Tables('ut_node').AddRow()
            self.__rastr.Tables('ut_node').Cols('ny').SetZ(i, node_num)
            self.__rastr.Tables('ut_node').Cols('tg').SetZ(i, recalc_tan)
        except Exception as e:
            return -1, e

        return i, None

    def set_node_pfvv_param(self, node_id: int,
                            param: str, value: float) -> Optional[str]:
        """
        set value of pfvv
        :param node_id: id of node
        :param param: str name of variance value ('pn', 'pg', ...)
        :param value: value of parameter
        :return: None - file was load successfully or COM Exception string
        """
        try:
            self.__rastr.Tables('ut_node').Cols(param).SetZ(node_id, value)
        except Exception as e:
            return e

        return None

    def get_branch_group_pf_value(self, bg_num: int) -> Optional[float]:
        """
        get sum power flow in branch group
        :param bg_num: number of branch group
        :return: float value of sum power flow in branch group
        """
        try:
            return float(self.__rastr.Tables('sechen') \
                         .Cols('psech').Z(self.__branch_groups[bg_num]))
        except:
            return None

    def power_flow(self, param: str = '') -> Optional[int]:
        """
        calculate power flow
        :param param: str param:
            '' - by default
            'p' - flot start
            'z' - no starting algo
            'c' - no data control
            'r' - no data prepare
        :return: Rastr return code or None if COM exception raised
             Rastr return code - 0 success, 1 - bad convergence (no pf)
        """
        try:
            return int(self.__rastr.rgm(param))
        except:
            return None

    def calc_max_power_flow(self, iters_count: int = 100,
                            check_parameters: int = 0x000,
                            margin_u: float = 0.5) -> int:
        """
        calculate maximum transmission power flow along the pfvv
        :param iters_count: maximum iterations count
        :param check_parameters: hex byte flag to set up control params of max PF calculating
        (001 - current, 010 - powerflow, 100 - voltage)
        :param margin_u: fraction from the nominal voltage, at which PF calculating stops 
        :return: 0 - success, -1 - failed 
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
        change state of branch via 'sta' 'vetv' table field 
        :param ip: branch begin node
        :param iq: branch end node
        :param np: parallel branch number
        :param state: str param, where '0' - switch on, '1' - switch off
        :return: 0 - if no com exception, -1 - com exception raised
        """
        try:
            vetv = self.__rastr.Tables('vetv')
            vetv.SetSel('ip={_ip}&iq={_iq}&np={_np}'.format(_ip=ip, _iq=iq, _np=np))
            vetv.Cols('sta').Calc(state)
        except:
            return -1
        return 0

    def swap_current_limits(self) -> int:
        """
        swap normal and emergency current limits, cause
        rastr can only consider normal current limits
        :return: 0 - if no com exception, -1 - com exception raised
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
