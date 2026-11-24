#!/bin/zsh
# Non-English labeling for the games given (tables are already built; cached batches are skipped).
cd "$(dirname "$0")"
for a in "$@"; do python3 label.py $a other; done
echo OTHER_LABELING_DONE
