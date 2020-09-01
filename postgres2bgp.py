#!/usr/bin/env python3

import sys
import json
import psycopg2
import time
import netaddr
import pgpubsub

def eprint(*args, **kwargs):
    print("[postgres2bgp]", *args, file=sys.stderr, **kwargs)

with open("/usr/local/etc/postgres2bgp.config.json", 'r') as _:
    config = json.loads(_.read())

eprint("Config loaded.")

conn_string = "dbname='{}' user='{}' host='{}' password='{}'".format(config['db_name'], config['db_user'], config['db_host'], config['db_pass'])

with psycopg2.connect(conn_string) as conn:
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
eprint("Connected to database on", config['db_host'])

pubsub = pgpubsub.connect(conn_string)
pubsub.listen('ip_list_updated')
eprint("Connected to Postgres event notification subsystem")

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

    #We are done, so let's wait for a notification.
    #We will wait a max of an hour, and then just update anyway (even if it will be a no-op).
    if next(pubsub.events(yield_timeouts=True, select_timeout=(60*60))) is None:
        eprint("No notification received in a while; doing a patrol update.")
    else:
        eprint("Got notification that a list had been updated, doing a normal update.")



