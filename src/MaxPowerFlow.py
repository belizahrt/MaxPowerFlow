from RastrSingleton import RastrInstance
import InitDataHelper

import sys


def ReadCmdLine(argv):
    params = {}

    i = 1
    while i < len(argv):
        if i >= len(argv)-1:
            break

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

checkIFlag = 0x001
checkPFlag = 0x010
checkVFlag = 0x100

if DoInitializeData(sys.argv) != -1:
    print('rgm = ', RastrInstance()._RastrInstance__rastr.rgm(''))
    RastrInstance().CalcMaxPowerFlow(300)
    RastrInstance().RestorePFToggle()
    RastrInstance().SaveAll('test')
else:
    print('Something wrong with CMD arguments!')
    HelpMessage()

