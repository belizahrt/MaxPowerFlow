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


def DoInitializeData(argv):
    
    params = ReadCmdLine(argv)

    rgFilesHandler = InitDataHelper.RegimeFilesHandler()
    bgFileHandler = InitDataHelper.BranchGroupsFilesHandler()
    outageFileHandler = InitDataHelper.OutagesFilesHandler()
    pfvvFileHandler = InitDataHelper.PFVVFilesHandler()

    rgFilesHandler.SetNext(bgFileHandler).SetNext(outageFileHandler) \
        .SetNext(pfvvFileHandler)

    for key in params:
        status = rgFilesHandler.Handle(key, params[key])
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
    return result


if DoInitializeData(sys.argv) != -1:

    criteria1 = 0.8 * abs(GetMaxPF()) - nonRegularLoad
    print('• 20% Pmax запас в нормальном режиме:\t', criteria1)
    
    criteria2 = abs(GetMaxPF(checkVFlag, 0.7/(1-0.15))) - nonRegularLoad
    print('• 15% Ucr запас в нормальном режиме:\t', criteria2)   

    criteria3 = abs(GetMaxPF(checkIFlag)) - nonRegularLoad
    print('• ДДТН в нормальном режиме:\t\t', criteria3)   
    
    RastrInstance().SaveAll('test')
else:
    print('Something wrong with CMD arguments!')
    HelpMessage()

