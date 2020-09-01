# postgres2bgp

Does what it says on the tin.

Well, sort of. It's really postgres2exabgp but the name was already getting way too long.

## Background

This is really designed to implement remotely-triggered black hole functionality over BGP.

[Cisco has a good document on this](https://www.cisco.com/c/dam/en_us/about/security/intelligence/blackhole.pdf). But, they want you to use an IOS box as what they call the "trigger." We implement the trigger in ExaBGP instead.

## Setup on this box

* Put this repo in /opt/postgres2bgp and make a new Python3 virtual environment in /opt/postgres2bgp/venv
* `source /opt/postgres2bgp/venv/bin/activate`
* `pip install -r /opt/postgres2bgp/requirements.txt`
* Add this to your exabgp config.

```
process postgres2bgp {
 run /opt/postgres2bgp/exabgp_process.sh;
 encoder text;
}
```

* Build a /usr/local/etc/postgres2bgp.config.json file like this.

```
{
 "db_user": "postgres2bgp",
 "db_pass": "hunter2",
 "db_host": "example.com",
 "db_name": "ip_lists", 

 "asn": 64824,
 "bh_community": 666
}
```

* Restart exabgp

## Setup on your edge routers

```
interface InternetFacingInterface1/1
 ip verify unicast source reachable-via any allow-default
!
interface InternetFacingInterface1/2
 ip verify unicast source reachable-via any allow-default
!
ip community-list standard BLACKHOLE permit 64824:666
ip route 192.18.66.66 255.255.255.255 Null0
route-map RTBH permit 10
 match community BLACKHOLE
 set ip next-hop 192.18.66.66
!
route-map NOTHING deny 10
 description deny everything
!
router bgp 64824
 !iBGP peering to the server
 neighbor 146.229.0.0 remote-as 64824
 neighbor 146.229.0.0 description ExaBGP-server
 address-family ipv4
  neighbor 146.229.0.0 soft-reconfiguration inbound
  neighbor 146.229.0.0 route-map RTBH in
  neighbor 146.229.0.0 route-map NOTHING out
  neighbor 146.229.0.0 activate
 exit-address-family
!

## Read these tips

* If you write to the table and then run "NOTIFY ip_list_updated;" then this app will immediately update the ExaBGP RIB, you don't have to wait for a timeout or anything.

