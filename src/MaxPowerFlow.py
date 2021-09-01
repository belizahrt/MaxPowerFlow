from RastrSingleton import RastrInstance
import InitDataHelper

import sys

# test branch
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

    rgFilesHandler.SetNext(bgFileHandler).SetNext(outageFileHandler)

    for key in params:
        if rgFilesHandler.Handle(key, params[key]) != None:
            return -1

    return 0


if DoInitializeData(sys.argv) != -1:
    print('rgm = ', RastrInstance()._RastrInstance__rastr.rgm(''))
    RastrInstance().SaveAll('test')
else:
    print('Failed to initialize data from args')
