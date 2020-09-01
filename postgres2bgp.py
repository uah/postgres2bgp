#!/usr/bin/env python3

import sys
import json
import psycopg2
import time
import netaddr

def eprint(*args, **kwargs):
    print("[postgres2bgp]", *args, file=sys.stderr, **kwargs)

with open("/usr/local/etc/postgres2bgp.config.json", 'r') as _:
    config = json.loads(_.read())

eprint("Config loaded.")

with psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(config['db_name'], config['db_user'], config['db_host'], config['db_pass'])) as conn:
    cursor = conn.cursor()

eprint("Connected to database on", config['db_host'])

prefixes_loaded = []

while True:
    eprint("Going to insert/withdraw prefixes now.")

    prefixes_to_load = []
    cursor.execute("select distinct srcaddr from ti_event where now() > start_stamp and now() < end_stamp order by srcaddr;")
    for row in cursor:
        prefixes_to_load.append(netaddr.IPNetwork(row[0]))

    eprint("The original IP list has", len(prefixes_to_load), "prefixes")
    prefixes_to_load = netaddr.cidr_merge(prefixes_to_load)
    eprint("This summarizes to", len(prefixes_to_load), "prefixes")

    prefixes_to_announce = [prefix for prefix in prefixes_to_load if prefix not in prefixes_loaded]
    prefixes_to_withdraw = [prefix for prefix in prefixes_loaded if prefix not in prefixes_to_load]

    eprint("Going to announce", len(prefixes_to_announce), "prefixes and withdraw", len(prefixes_to_withdraw), "prefixes")

    for prefix in prefixes_to_announce:
        cmd = "announce route {} next-hop 192.18.66.66 community [no-export {}:{}]".format(prefix, config['asn'], config['bh_community'])
        print(cmd)
        
    for prefix in prefixes_to_withdraw:
        cmd = "withdraw route {} next-hop 192.18.66.66 community [no-export {}:{}]".format(prefix, config['asn'], config['bh_community'])
        print(cmd)

    eprint("updates have been sent to exabgp.")
    prefixes_loaded = prefixes_to_load

    time.sleep(15*60) #It's only going to be like this til we have subscriptions
