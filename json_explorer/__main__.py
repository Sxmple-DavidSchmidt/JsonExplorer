#!/usr/bin/env python

from importlib.metadata import entry_points
from . import json_explorer

def main(argv=None):
    json_explorer.main(argv)
