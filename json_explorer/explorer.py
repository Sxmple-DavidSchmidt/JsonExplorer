#!/usr/bin/env python

import argparse
import json
import sys
from typing import List, Dict, Any, Tuple
from enum import Enum

import curses
import _curses

class DataConstants(Enum):
    LEAF_NODE = -1


class DataValue:
    content: Any
    content_type: type
    as_string: str

    def __init__(self, content: Any):
        self.content = content
        self.as_string = self.stringify_value(content)
        self.content_type = type(content)

    @staticmethod
    def stringify_value(value):
        if isinstance(value, str):
            return f'"{value}"'
        if isinstance(value, dict):
            if len(value.keys()) != 1:
                return f'Dictionary, {len(value.keys())} keys'
            return 'Dictionary, 1 key'
        if isinstance(value, list):
            if len(value) != 1:
                return f'List, {len(value)} entries'
            return 'List, 1 entry'
        return str(value)


class DataManager:
    data: Dict
    path: List[Tuple[Any, int]]
    pointer: int

    def __init__(self, data: Dict, path: List = None, pointer: int = 0):
        self.data = data
        self.path = path if path is not None else []
        self.pointer = pointer

    def get_data(self) -> list[tuple[DataValue, DataValue]]:
        def sort_dv_item(item: Tuple[DataValue, DataValue]):
            dv_key, dv_value = item
            if isinstance(dv_value.content, dict):
                return 2
            if isinstance(dv_value.content, list):
                return 1
            return 0

        cdata =  self._resolve_path(self.data, self.path)
        if isinstance(cdata, Dict):
            cdata = {DataValue(key): DataValue(value) for key, value in cdata.items()}
            cdata_items = sorted(sorted(cdata.items(), key=lambda item: item[0].as_string), key=sort_dv_item)
            return cdata_items
        if isinstance(cdata, List):
            return [(DataValue(index), DataValue(value)) for index, value in enumerate(cdata)]
        return [(DataValue(DataConstants.LEAF_NODE), DataValue(cdata))]

    def get_keys(self) -> List[DataValue]:
        return [item[0] for item in self.get_data()]

    def get_path(self) -> List[DataValue]:
        return [DataValue(entry[0]) for entry in self.path]

    def get_pointer(self) -> int:
        return self.pointer

    def move_up(self):
        if len(self.path) > 0:
            self.pointer = self.path[-1][1] if len(self.path) > 0 else 0
            self.path = self.path[:-1]


    def move_down(self):
        key, value = list(self.get_data())[self.pointer]
        if key.content == DataConstants.LEAF_NODE:
            return
        if isinstance(value.content, (dict, list)):
            self.path.append((key.content, self.pointer))
            self.pointer = 0

    def increment_pointer(self):
        self.pointer = (self.pointer + 1) % len(self.get_keys())

    def decrement_pointer(self):
        self.pointer = (self.pointer - 1) % len(self.get_keys())

    @staticmethod
    def _resolve_path(data: Dict, path: List) -> Dict:
        cdata = data
        for entry in [p[0] for p in path]:
            if isinstance(cdata, list):
                if isinstance(entry, int) and entry < len(cdata):
                    cdata = cdata[entry]
                else:
                    sys.exit(1)
            elif isinstance(cdata, dict):
                if entry in cdata:
                    cdata = cdata[entry]
                else:
                    sys.exit(1)
            else:
                sys.exit(1)
        return cdata


class DataRenderer:
    window: _curses.window
    dtm: DataManager

    def __init__(self, data_manager: DataManager):
        self.dtm = data_manager
        self.init_curses()
        try:
            self.main_loop()
        finally:
            self.kill_curses()

    def init_curses(self):
        self.window = curses.initscr()
        self.window.keypad(True)
        curses.noecho()
        curses.cbreak()

    def kill_curses(self):
        self.window.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def handle_keystroke(self, key: int):
        if key == curses.KEY_UP:
            self.dtm.decrement_pointer()
        elif key == curses.KEY_DOWN:
            self.dtm.increment_pointer()
        elif key == curses.KEY_LEFT:
            self.dtm.move_up()
        elif key == curses.KEY_RIGHT:
            self.dtm.move_down()

    def update_screen(self):
        path_str = '/'.join(['root'] + [entry.as_string for entry in self.dtm.get_path()])
        keys = self.dtm.get_keys()

        key_offset = 2  # Leave room for pointer
        value_offset = key_offset + 1 + max([0] + [len(key.as_string) for key in keys])

        self.window.clear()
        self.window.addstr(0, 0, path_str)

        # sort items:

        data_items = self.dtm.get_data()
        if len(data_items) == 0:
            self.window.addstr(1, key_offset, "Entry is empty")
        else:
            for index, (key, value) in enumerate(data_items, 1):
                if key.content == DataConstants.LEAF_NODE:
                    self.window.addstr(index, key_offset, value.as_string)
                else:
                    self.window.addstr(index, key_offset, key.as_string)
                    self.window.addstr(index, value_offset, value.as_string)

        self.window.addstr(self.dtm.get_pointer() + 1, 0, '>')
        self.window.refresh()

    def main_loop(self):
        while True:
            self.update_screen()
            keystroke = self.window.getch()
            if keystroke == ord('q'):
                break

            self.handle_keystroke(keystroke)


def main():
    parser = argparse.ArgumentParser(
        description='Python script to navigate big JSON objects in a TUI')
    parser.add_argument('file_path', type=str, help='Path of the json file')
    args = parser.parse_args()

    if args.file_path:
        try:
            with open(args.file_path, 'r') as file:
                json_string = file.read()
                json_dict = json.loads(json_string)
                DataRenderer(DataManager(json_dict))
        except FileNotFoundError:
            print(f"Could not find file {args.file_path}")
            exit(1)
