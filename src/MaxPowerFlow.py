from RastrSingleton import RastrInstance
import InitDataHelper

import sys


def ReadCmdLine(argv):
    params = {}

    i = 1
    while i < len(argv):
        if argv[i+1] not in params:
            params[argv[i]] = argv[i+1]
        i += 2
    
    return params

outages: dict = {}

def DoInitializeData(argv):
    global outages
    params = ReadCmdLine(argv)

    rgFilesHandler = InitDataHelper.RegimeFilesHandler()
    bgFileHandler = InitDataHelper.BranchGroupsFilesHandler()
    outageFileHandler = InitDataHelper.OutagesFilesHandler()
    pfvvFileHandler = InitDataHelper.PFVVFilesHandler()

    rgFilesHandler.SetNext(bgFileHandler).SetNext(outageFileHandler) \
        .SetNext(pfvvFileHandler)

    for key in params:
        status = rgFilesHandler.Handle(key, params[key])

        if key == '-outages':
            outages = eval(status)
            status = None

        if status != None:
            print('Data initialization failed: ', status)
            return -1

    return 0


def HelpMessage():
    print('Just use this CMD template: ')
    print('MaxPowerFlow.py [-KEY1] <ARG1> [-KEY2] <ARG2> ..., where KEY and ARG:')
    print('\t -rg2 <path> - regime file path')
    print('\t -rg2template <path> - regime template file path')
    print('\t -bg <path> - branch group (json) file path')
    print('\t -outages <path> - outages (json) file path')
    print('\t -pfvv <path> - power flow vector variance (csv) file path')


####################################################################

nonRegularLoad = 30

maxIters = 300

checkIFlag = 0x001
checkPFlag = 0x010
checkVFlag = 0x100

def GetMaxPF(checkParams=0x000, marginU=0.5):
    RastrInstance().CalcMaxPowerFlow(maxIters, checkParams, marginU)
    result = RastrInstance().GetBranchGroupPFValue(1)
    RastrInstance().RestorePFToggle()
    return abs(result)


def GetEmergencyPF(checkParams=0x000, marginU=0.5, marginP=1):
    global outages
    global maxIters

    faults_result = []
    for outage in outages:
        RastrInstance().ChangeBranchState(
            outages[outage]['ip'], outages[outage]['iq'], 0, '1')

        RastrInstance().CalcMaxPowerFlow(maxIters, checkParams, marginU)
        pos = RastrInstance().GetTogglePositionsCount()

        limP = abs(RastrInstance().GetBranchGroupPFValue(1))
        while abs(RastrInstance().GetBranchGroupPFValue(1)) > marginP * limP:
            pos -= 1
            RastrInstance().RestorePFToggle(pos)

        RastrInstance().ChangeBranchState(
            outages[outage]['ip'], outages[outage]['iq'], 0, '0')

        RastrInstance().PowerFlow()
        faults_result.append(abs(RastrInstance().GetBranchGroupPFValue(1)))
        
        RastrInstance().RestorePFToggle()
        RastrInstance().ChangeBranchState(
            outages[outage]['ip'], outages[outage]['iq'], 0, '0')
        RastrInstance().PowerFlow()

    return min(faults_result)


if DoInitializeData(sys.argv) != -1:

    criteria1 = 0.8 * GetMaxPF() - nonRegularLoad
    print('• 20% Pmax запас в нормальном режиме:\t', round(criteria1, 2))
    
    criteria2 = GetMaxPF(checkVFlag, 0.7/(1-0.15)) - nonRegularLoad
    print('• 15% Ucr запас в нормальном режиме:\t', round(criteria2, 2))   

    criteria3 = GetMaxPF(checkIFlag) - nonRegularLoad
    print('• ДДТН в нормальном режиме:\t\t', round(criteria3, 2))   
    
    criteria4 = GetEmergencyPF(marginP=0.92) - nonRegularLoad
    print('• 8% Pmax запас в послеаварийном режиме:', round(criteria4, 2)) 

    criteria5 = GetEmergencyPF(
        checkParams=checkVFlag, marginU=0.7/(1-0.1)) - nonRegularLoad
    print('• 10% Ucr запас в послеаварийном режиме:', round(criteria5, 2)) 

    RastrInstance().SwapCurrentLimits()
    criteria6 = GetEmergencyPF(checkParams=checkIFlag) - nonRegularLoad
    RastrInstance().SwapCurrentLimits()
    print('• АДТН в послеаварийном режиме:\t\t', round(criteria6, 2)) 

else:
    print('Something wrong with CMD arguments!')
    HelpMessage()

