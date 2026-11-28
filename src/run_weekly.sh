#!/bin/bash
# The weekly run. Free: no model calls. Sends nothing unless you add --send.
#   ./run_weekly.sh            refresh from Steam, recompute, rebuild the site, verify
#   ./run_weekly.sh --offline  skip the Steam refresh (recompute from the local tables)
#   ./run_weekly.sh --send     also post this week's alerts to the webhooks in src/webhooks.json
set -e
cd "$(dirname "$0")"
if [[ " $* " != *" --offline "* ]]; then python3 refresh.py; fi
python3 after_review.py && python3 after_review.py --all
python3 fans.py && python3 fans.py --all
python3 monitor.py > /dev/null
python3 benchmark.py > /dev/null
if [[ " $* " == *" --send "* ]]; then python3 alerts.py --send; else python3 alerts.py; fi
python3 export.py
python3 build_site.py
python3 build_product.py
python3 digest.py
python3 verify_product.py
echo WEEKLY_RUN_DONE
