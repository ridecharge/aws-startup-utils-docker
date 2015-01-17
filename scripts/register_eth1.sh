#!/bin/sh
cat /etc/network/interfaces.d/eth0.cfg | sed 's/eth0/eth1/g' > /etc/network/interfaces.d/eth1.cfg
ifup eth1
echo "200 out" >> /etc/iproute2/rt_tables
GATEWAY=$(route -n | awk 'FNR == 3 {print $2}')
PRIVATE_IP=$(ifconfig -a | grep -A 1 eth1 | awk 'FNR == 2 { print $2 }' | sed 's/.*://')
ip route add default via $GATEWAY dev eth1 table out
ip rule add from $PRIVATE_IP/32 table out
ip rule add to $PRIVATE_IP/32 table out
ip route flush cache
