#!/usr/bin/env python3

import sys
import json
import psycopg2
import time

def eprint(*args, **kwargs):
    print("[postgres2bgp]", *args, file=sys.stderr, **kwargs)

with open("/usr/local/etc/postgres2bgp.config.json", 'r') as _:
    config = json.loads(_.read())

eprint("Config loaded.")

with psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(config['db_name'], config['db_user'], config['db_host'], config['db_pass'])) as conn:
    cursor = conn.cursor()

eprint("Connected to database on", config['db_host'])

eprint("About to do initial prefix load.")

cursor.execute("select distinct srcaddr from ti_event where now() > start_stamp and now() < end_stamp order by srcaddr;")
eprint("Loading", cursor.rowcount, "prefixes")
for row in cursor:
    ip = row[0]
    #TODO: summarize
    cmd = "announce route {}/32 next-hop 192.18.66.66 community [no-export {}:{}]".format(ip, config['asn'], config['bh_community'])
    print(cmd)

while True:
    time.sleep(1000)
