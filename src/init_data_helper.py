from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

import json
import csv

from rastr_singleton import RastrInstance


# interface of base class of chain of responsibility
class IDataHandler(ABC):
    @abstractmethod
    def set_next(self, handler: IDataHandler) -> IDataHandler:
        pass

    @abstractmethod
    def handle(self, data_source: str, data: str) -> Optional[str]:
        pass


class AbstractHandler(IDataHandler):
    _next_handler: IDataHandler = None

    def set_next(self, handler: IDataHandler) -> IDataHandler:
        """
        method sets up next handler in the chain,
        which is called when the current handler cannot handle data
        :param handler: next handle IDataHandler class
        :return: next handler instance
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, data_source: str, data: str) -> Optional[str]:
        """
        pass data in next handler
        :param data_source: source of data (data key)
        :param data: data, path to file for example
        :return: result of next handler executing or string error if handler was last
        """
        if self._next_handler:
            return self._next_handler.handle(data_source, data)

        return 'No data handler for ' + data_source


# handler for .rg2 regime & regime template files
class RegimeFilesHandler(AbstractHandler):
    __rg2_file: Optional[str] = None
    __rg2_template_file: Optional[str] = None

    def handle(self, data_source: str, data: str) -> Optional[str]:
        # waiting for linked param (-rg2 + -rg2template)
        if data_source == "-rg2":
            self.__rg2_file = data
            if self.__rg2_template_file is None:
                return None
        elif data_source == "-rg2template":
            self.__rg2_template_file = data
            if self.__rg2_file is None:
                return None

        if self.__rg2_file and self.__rg2_template_file:
            result = RastrInstance() \
                .load(self.__rg2_file, self.__rg2_template_file)
            self.__rg2_file = None
            self.__rg2_template_file = None
            return result
        else:
            return super().handle(data_source, data)


# base class for json files handlers
class JsonFilesHandler(AbstractHandler):

    @staticmethod
    def _read_json(path):
        with open(path, "r") as read_file:
            result = json.load(read_file)

        return result

    def handle(self, data_source: str, data: str) -> Optional[str]:
        return super().handle(data_source, data)


# handler for flow gates files (.json)
class BranchGroupsFilesHandler(JsonFilesHandler):

    def handle(self, data_source: str, data: str) -> Optional[str]:
        status = None
        if data_source == "-bg":
            branches = self._read_json(data)

            for branch in branches:
                bg_num = 1

                if bg_num not in RastrInstance().get_branch_groups():
                    RastrInstance().make_branch_group(
                        bg_num,
                        'MaxPFBranchGroup ' + str(bg_num))

                status = RastrInstance().add_branch_to_branch_group(
                    bg_num,
                    branches[branch].get('ip', 0),
                    branches[branch].get('iq', 0))

            return status
        else:
            return super().handle(data_source, data)


# handler for outages files (.json)
class OutagesFilesHandler(JsonFilesHandler):

    def handle(self, data_source: str, data: str) -> Optional[str]:
        if data_source == "-outages":
            return str(self._read_json(data))
        else:
            return super().handle(data_source, data)


# handler for power flow node variance vector files (.csv)
class PFVVFilesHandler(AbstractHandler):
    __node_id_map: dict = {}

    def handle(self, data_source: str, data: str) -> Optional[str]:
        status = None
        if data_source == "-pfvv":
            with open(data) as csv_file:
                reader = csv.DictReader(csv_file)

                for row in reader:
                    node = row.get('node', 0)
                    if node not in self.__node_id_map:
                        node_id, status = RastrInstance().add_node_pfvv(node, row.get('tg', 0))
                        self.__node_id_map[node] = node_id
                    else:
                        node_id = self.__node_id_map[node]

                    variable = row.get('variable', 'pn')
                    status = RastrInstance() .set_node_pfvv_param(
                        node_id, variable, float(row.get('value', 0)))

            return status
        else:
            return super().handle(data_source, data)
