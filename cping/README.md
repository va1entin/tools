# cping.sh

cping *c*ontinously *ping*s a certain port at an IP address.
Pinging is not really the correct description, because it actually just checks whether the port is open using nmap instead of true pingin via ICMP.

My main use case for this is checking if/when a host or service is back up after having triggered a restart.

```
cping.sh 22 192.168.1.2
```
