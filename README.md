# AT&T Arris Router Bandwidth Scraper

## Purpose

Collect the WAN bandwidth metrics for the AT&T U-Verse Pace 5628AC home router.

Publish these metric to an InfluxDB time series database.

## Metrics Collected

From: `http://192.168.1.254/xslt?PAGE=C_1_0`
1. TX Packet Count
2. TX Byte Count
3. TX Packet Error Count
4. TX Packet Error %

5. RX Packet Count
6. RX Byte Count
7. RX Packet Error Count
8. RX Packet Error %

From: `http://192.168.1.254/xslt?PAGE=C_5_5`

9. NAT Connection Count
10. NAT Connection % Used

## Implementation

Import configuration with TOML (because it's what's cool with kids these days)
Scrape router HTML page (unathenticated) with requests
Parse HTML and tables with BeautifulSoup (beautifulsoup4)
Send data to InfluxDB (TBD on JSON vs Line Protocol)

## Configurable Parameters

- Router IP
- InfluxDB IP
- InfluxDB Password
- InfluxDB Certificate
  - Or just bypass cert checks?
