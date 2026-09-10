#!/bin/sh
set -e

# prvotne stiahnutie pri starte, nech sa nečaká do 3:00
python3 /app/scrape_odpad.py || echo "prvotny scrape zlyhal, skusi sa znova o 3:00"

# cron na pozadi (denne obnovovanie)
crond -b -l 8

# staticky httpd na popredi, drzi kontajner nazivo
exec httpd -f -p 8080 -h /app
