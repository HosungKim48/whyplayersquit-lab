#!/bin/zsh
# For each game: wait for its fetch to finish, build the local table, then label it.
cd "$(dirname "$0")"
for a in 1295660 949230 1272080 2054970 2246340 1716740; do
  while ! grep -q "$a DONE" ../data/work/fetch_*.log 2>/dev/null; do sleep 30; done
  python3 build_dataset.py $a
  python3 label.py $a
done
echo ALL_LABELING_DONE
