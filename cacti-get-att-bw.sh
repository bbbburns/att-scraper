#!/bin/sh
# Get the bytes TX and RX from the ATT ARRIS 5628AC
HTMLSTRING=""

HTMLSTRING=`curl --crlf -s http://192.168.1.254/xslt?PAGE=C_1_0 \
| egrep --after-context=11 "Transmit"`

#TX Bytes - Line 2
TXBYTES=`echo "$HTMLSTRING" | sed -n '2p' | egrep -o "[[:digit:]]+"`
#echo "TXBYTES:$TXBYTES"

#TX Pkts - Line 3
TXPKTS=`echo "$HTMLSTRING" | sed -n '3p' | egrep -o "[[:digit:]]+"`
#echo "TXPKTS:$TXPKTS"

#TX Errors - Line 4
TXERR=`echo "$HTMLSTRING" | sed -n '4p' | egrep -o "[[:digit:]]+"`

#TX Error % - Line 5

#RX Bytes - Line 9
RXBYTES=`echo "$HTMLSTRING" | sed -n '9p' | egrep -o "[[:digit:]]+"`
#echo "RXBYTES:$RXBYTES"

#RX Pkts - Line 10
RXPKTS=`echo "$HTMLSTRING" | sed -n '10p' | egrep -o "[[:digit:]]+"`
#echo "RXPKTS:$RXPKTS"

#RX Errors - Line 11
RXERR=`echo "$HTMLSTRING" | sed -n '11p' | egrep -o "[[:digit:]]+"`

#RX Error % - Line 12
echo "TXBYTES:$TXBYTES TXPKTS:$TXPKTS TXERR:$TXERR RXBYTES:$RXBYTES RXPKTS:$RXPKTS RXERR:$RXERR"

echo "`date`: ATT ARRIS FOUND:" >> /tmp/cacti-run.log
echo "  TXBYTES:$TXBYTES TXPKTS:$TXPKTS TXERR:$TXERR RXBYTES:$RXBYTES RXPKTS:$RXPKTS RXERR:$RXERR" >> /tmp/cacti-run.log
