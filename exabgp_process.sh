#!/usr/bin/env bash

THEDIR="$(dirname $(readlink -f "$0"))"

PYTHONUNBUFFERED=TRUE
export PYTHONUNBUFFERED
$THEDIR/venv/bin/python $THEDIR/postgres2bgp.py
