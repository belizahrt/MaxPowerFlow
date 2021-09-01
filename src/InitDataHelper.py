from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

import json

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
    def Handle(self, dataSource: str, data: str) -> int:
        if self._next_handler:
            return self._next_handler.Handle(dataSource, data)
        
        return -1


class RegimeFilesHandler(AbstractHandler):
    __rg2File: str = None
    __rg2TemplateFile: str = None

    def Handle(self, dataSource: str, data: str) -> int:
        if dataSource == "-rg2":
            self.__rg2File = data
            if self.__rg2TemplateFile == None:
                return 0
        elif dataSource == "-rg2template":
            self.__rg2TemplateFile = data
            if self.__rg2File == None:
                return 0

        if self.__rg2File and self.__rg2TemplateFile:
            result = RastrInstance().Load(self.__rg2File, self.__rg2TemplateFile)
            self.__rg2File = None
            self.__rg2TemplateFile = None
            return result
        else:
            return super().Handle(dataSource, data)


class BranchGroupsFilesHandler(AbstractHandler):

    def __readJson(self, path):
        result = {}

        with open(path, "r") as read_file:
            result = json.load(read_file)

        return result

    def Handle(self, dataSource: str, data: str) -> int:
        if dataSource == "-bg":
            branches = self.__readJson(data)
            RastrInstance().MakeBranchGroup(branches)
            return 0
        else:
            return super().Handle(dataSource, data)