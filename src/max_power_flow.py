import sys
import os

module_path = os.path.abspath(os.getcwd())    

if module_path not in sys.path:       
    sys.path.append(module_path)

from rastr_singleton import RastrInstance
import init_data_helper


outages: dict = {}


def read_cmd_line(argv: [str]) -> dict:
    """
    read list of cmd args to dict in format {KEY: ARG} (see help message)
    :param argv: list of cmd arguments
    :return: map of arguments
    """
    params = {}

    i = 1
    while i < len(argv) - 1:
        if argv[i + 1] not in params:
            params[argv[i]] = argv[i + 1]
        i += 2

    return params


def cmd_params_assert(params: [str]) -> bool:
    """
    function asserts cmd params and necessary params in template
    :param params: list of cmd arguments
    :return: True if lists have the same values
    """
    template = ['-rg2', '-rg2template', '-bg', '-outages', '-pfvv']

    return sorted(template) == sorted(params)


def build_data_handler() -> init_data_helper.IDataHandler:
    """
    function builds data handler
    :return: Data handler interface with initialized chain
    """
    rg_files_handler = init_data_helper.RegimeFilesHandler()
    bg_files_handler = init_data_helper.BranchGroupsFilesHandler()
    outages_files_handler = init_data_helper.OutagesFilesHandler()
    pfvv_files_handler = init_data_helper.PFVVFilesHandler()

    rg_files_handler \
        .set_next(bg_files_handler) \
        .set_next(outages_files_handler) \
        .set_next(pfvv_files_handler)

    return rg_files_handler


def do_initialize_data(argv: [str]) -> int:
    """
    function extracts init data from cmd args via helper
    :param argv: list of cmd arguments
    :return: 0 - if init ok, -1 - initialization failed
    """
    global outages

    params = read_cmd_line(argv)
    if not cmd_params_assert(params.keys()):
        return -1

    data_handler = build_data_handler()
    for key in params:
        status = data_handler.handle(key, params[key])

        if key == '-outages':
            outages = eval(status)
            status = None

        if status is not None:
            print('Data initialization failed: ', status)
            return -1

    return 0


def help_message() -> None:
    """
    prints help message of usage format
    """
    print('Just use this CMD template: ')
    print('MaxPowerFlow.py [-KEY1] <ARG1> [-KEY2] <ARG2> ..., '
        'where KEY and ARG:')
    print('\t -rg2 <path> - regime file path')
    print('\t -rg2template <path> - regime template file path')
    print('\t -bg <path> - branch group (json) file path')
    print('\t -outages <path> - outages (json) file path')
    print('\t -pfvv <path> - power flow vector variance (csv) file path')


####################################################################

non_regular_load: float = 30.0

max_iters: int = 300

check_i_flag: int = 0x001
check_p_flag: int = 0x010
check_v_flag: int = 0x100


def get_max_pf(check_params: int = 0x000, margin_u: float = 0.5) -> float:
    """
    wrapper method for calculate and extract value of max transmission
    power flow
    ! restore origin PF state
    :param check_params: hex byte flag to set up control params of
    max PF calculating
        (001 - current, 010 - powerflow, 100 - voltage)
    :param margin_u: fraction from the nominal voltage, at which PF
    calculating stops
    :return: abs value of power flow in branch group at id = 1
    """
    global max_iters

    RastrInstance().calc_max_power_flow(max_iters, check_params, margin_u)
    result = RastrInstance().get_branch_group_pf_value(1)
    RastrInstance().restore_pf_toggle()
    return abs(result)


def get_emergency_pf(check_params: int = 0x000,
                     margin_u: float = 0.5,
                     margin_p: float = 1) -> float:
    """
    wrapper method for calculate and extract value of emergency
    (cause ref. disturbances) transmission power flow
    ! restore origin PF state
    :param check_params: hex byte flag to set up control params of
    max PF calculating
        (001 - current, 010 - powerflow, 100 - voltage)
    :param margin_u: fraction from the nominal voltage, at which
    PF calculating stops
    :param margin_p: fraction of P in emergency PF should be roll back
    before restore PF
    :return: min abs value as result of outages permutation
        of power flow in branch group at id = 1
    """
    global outages
    global max_iters

    faults_result = []
    for outage in outages:
        RastrInstance().change_branch_state(
            outages[outage]['ip'], outages[outage]['iq'], 0, '1')

        RastrInstance().calc_max_power_flow(max_iters, check_params, margin_u)
        pos = RastrInstance().get_toggle_positions_count()

        lim_p = abs(RastrInstance().get_branch_group_pf_value(1))
        while abs(RastrInstance().get_branch_group_pf_value(1)
                  ) > margin_p * lim_p:
            pos -= 1
            RastrInstance().restore_pf_toggle(pos)

        RastrInstance().change_branch_state(
            outages[outage]['ip'], outages[outage]['iq'], 0, '0')

        RastrInstance().power_flow()
        faults_result.append(abs(RastrInstance().get_branch_group_pf_value(1)))

        RastrInstance().restore_pf_toggle()
        RastrInstance().change_branch_state(
            outages[outage]['ip'], outages[outage]['iq'], 0, '0')
        RastrInstance().power_flow()

    return min(faults_result)


####################################################################
# main

if do_initialize_data(sys.argv) != -1:

    criteria1 = 0.8 * get_max_pf() - non_regular_load
    print('??? 20% Pmax ?????????? ?? ???????????????????? ????????????:\t', round(criteria1, 2))

    criteria2 = get_max_pf(check_v_flag, 0.7 / (1 - 0.15)) - non_regular_load
    print('??? 15% Ucr ?????????? ?? ???????????????????? ????????????:\t', round(criteria2, 2))

    criteria3 = get_max_pf(check_i_flag) - non_regular_load
    print('??? ???????? ?? ???????????????????? ????????????:\t\t', round(criteria3, 2))

    criteria4 = get_emergency_pf(margin_p=0.92) - non_regular_load
    print('??? 8% Pmax ?????????? ?? ???????????????????????????? ????????????:', round(criteria4, 2))

    criteria5 = get_emergency_pf(
        check_params=check_v_flag, margin_u=0.7 / (1 - 0.1)) - non_regular_load
    print('??? 10% Ucr ?????????? ?? ???????????????????????????? ????????????:', round(criteria5, 2))

    RastrInstance().swap_current_limits()
    criteria6 = get_emergency_pf(check_params=check_i_flag) - non_regular_load
    RastrInstance().swap_current_limits()
    print('??? ???????? ?? ???????????????????????????? ????????????:\t\t', round(criteria6, 2))

else:
    print('Something wrong with CMD arguments!')
    help_message()
