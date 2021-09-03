from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

import json
import csv

from RastrSingleton import RastrInstance

class IDataHandler(ABC):
    @abstractmethod
    def SetNext(self, handler: IDataHandler) -> IDataHandler:
        pass

    @abstractmethod
    def Handle(self, dataSource, data: str) -> Optional[int]:
        pass


class AbstractHandler(IDataHandler):
    _next_handler: IDataHandler = None

    def SetNext(self, handler: IDataHandler) -> IDataHandler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def Handle(self, dataSource: str, data: str) -> str:
        if self._next_handler:
            return self._next_handler.Handle(dataSource, data)
        
        return 'No data handler for ' + dataSource


class RegimeFilesHandler(AbstractHandler):
    __rg2File: str = None
    __rg2TemplateFile: str = None

    def Handle(self, dataSource: str, data: str) -> str:
        # waiting for linked param (-rg2 + -rg2template)
        if dataSource == "-rg2":
            self.__rg2File = data
            if self.__rg2TemplateFile == None:
                return None
        elif dataSource == "-rg2template":
            self.__rg2TemplateFile = data
            if self.__rg2File == None:
                return None

        if self.__rg2File and self.__rg2TemplateFile:
            result = RastrInstance() \
                .Load(self.__rg2File, self.__rg2TemplateFile)
            self.__rg2File = None
            self.__rg2TemplateFile = None
            return result
        else:
            return super().Handle(dataSource, data)


class JsonFilesHandler(AbstractHandler):

    def _readJson(self, path):
        result = {}

        with open(path, "r") as read_file:
            result = json.load(read_file)

        return result

    def Handle(self, dataSource: str, data: str) -> str:
        super().Handle(dataSource, data)


class BranchGroupsFilesHandler(JsonFilesHandler):

    def Handle(self, dataSource: str, data: str) -> str:
        status = None
        if dataSource == "-bg":
            branches = self._readJson(data)

            for branch in branches:
                bgNum = 1 #branches[branch].get('np', 0)

                if bgNum not in RastrInstance().GetBranchGroups():
                    status = RastrInstance().MakeBranchGroup(
                        bgNum, 
                        'MaxPFBranchGroup ' + str(bgNum))

                status = RastrInstance().AddBranchToBranchGroup(
                    bgNum, 
                    branches[branch].get('ip', 0), 
                    branches[branch].get('iq', 0))

            return status
        else:
            return super().Handle(dataSource, data)


class OutagesFilesHandler(JsonFilesHandler):

    def Handle(self, dataSource: str, data: str) -> str:
        if dataSource == "-outages":
            return RastrInstance().SetOutages(self._readJson(data))
        else:
            return super().Handle(dataSource, data)


class PFVVFilesHandler(AbstractHandler):
    __nodeIdMap: dict = {}

    def Handle(self, dataSource: str, data: str) -> str:
        status = None
        if dataSource == "-pfvv":
            with open(data) as csvfile:
                reader = csv.DictReader(csvfile)

                id = -1
                for row in reader:
                    node = row.get('node', 0)
                    if node not in self.__nodeIdMap:
                        id, status = RastrInstance().AddNodePFVV(node, row.get('tg', 0))
                        self.__nodeIdMap[node] = id
                    else:
                        id = self.__nodeIdMap[node]
                        
                    variable = row.get('variable', 'pn')
                    status = RastrInstance() \
                        .SetNodePFVVParam(id, variable, float(row.get('value', 0)))

            return status
        else:
            return super().Handle(dataSource, data)