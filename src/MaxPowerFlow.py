from RastrSingleton import RastrInstance
import InitDataHelper

import sys


outages: dict = {}


def read_cmd_line(argv: [str]) -> dict:
    """

    :param argv:
    :return:
    """
    params = {}

    i = 1
    while i < len(argv):
        if argv[i + 1] not in params:
            params[argv[i]] = argv[i + 1]
        i += 2

    return params


def do_initialize_data(argv: [str]) -> int:
    """

    :param argv:
    :return:
    """
    global outages
    params = read_cmd_line(argv)

    rg_files_handler = InitDataHelper.RegimeFilesHandler()
    bg_files_handler = InitDataHelper.BranchGroupsFilesHandler()
    outages_files_handler = InitDataHelper.OutagesFilesHandler()
    pfvv_files_handler = InitDataHelper.PFVVFilesHandler()

    rg_files_handler.set_next(bg_files_handler).set_next(outages_files_handler) \
        .set_next(pfvv_files_handler)

    for key in params:
        status = rg_files_handler.handle(key, params[key])

        if key == '-outages':
            outages = eval(status)
            status = None

        if status is not None:
            print('Data initialization failed: ', status)
            return -1

    return 0


def help_message() -> None:
    """

    """
    print('Just use this CMD template: ')
    print('MaxPowerFlow.py [-KEY1] <ARG1> [-KEY2] <ARG2> ..., where KEY and ARG:')
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

    :param check_params:
    :param margin_u:
    :return:
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

    :param check_params:
    :param margin_u:
    :param margin_p:
    :return:
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
        while abs(RastrInstance().get_branch_group_pf_value(1)) > margin_p * lim_p:
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
    print('• 20% Pmax запас в нормальном режиме:\t', round(criteria1, 2))

    criteria2 = get_max_pf(check_v_flag, 0.7 / (1 - 0.15)) - non_regular_load
    print('• 15% Ucr запас в нормальном режиме:\t', round(criteria2, 2))

    criteria3 = get_max_pf(check_i_flag) - non_regular_load
    print('• ДДТН в нормальном режиме:\t\t', round(criteria3, 2))

    criteria4 = get_emergency_pf(margin_p=0.92) - non_regular_load
    print('• 8% Pmax запас в послеаварийном режиме:', round(criteria4, 2))

    criteria5 = get_emergency_pf(
        check_params=check_v_flag, margin_u=0.7 / (1 - 0.1)) - non_regular_load
    print('• 10% Ucr запас в послеаварийном режиме:', round(criteria5, 2))

    RastrInstance().swap_current_limits()
    criteria6 = get_emergency_pf(check_params=check_i_flag) - non_regular_load
    RastrInstance().swap_current_limits()
    print('• АДТН в послеаварийном режиме:\t\t', round(criteria6, 2))

else:
    print('Something wrong with CMD arguments!')
    help_message()
