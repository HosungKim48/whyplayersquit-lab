#!/bin/zsh
# Second stream: same job as run_labeling.sh but from the end of the list (cached batches are skipped by both).
cd "$(dirname "$0")"
for a in 1716740 2246340; do
  while ! grep -q "$a DONE" ../data/work/fetch_*.log 2>/dev/null; do sleep 30; done
  python3 build_dataset.py $a
  python3 label.py $a
done
echo REV_LABELING_DONE
