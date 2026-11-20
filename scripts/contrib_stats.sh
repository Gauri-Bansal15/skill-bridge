#!/usr/bin/env bash
# Shows who committed what. Run after the team has pushed real commits.
# Tip: every member should set their own name in git (git config user.name "...").
set -euo pipefail
echo "== Commits per author =="
git shortlog -sne --no-merges HEAD
echo
echo "== Lines added / removed per author =="
git log --no-merges --pretty='AUTHOR:%an' --numstat | awk '
  /^AUTHOR:/ {a=substr($0,8); next}
  NF==3 && $1 ~ /^[0-9]+$/ {add[a]+=$1; del[a]+=$2}
  END {for (k in add) printf "%-25s +%d  -%d\n", k, add[k], del[k]}'
echo
echo "== Files touched per author =="
for a in $(git log --format='%an' | sort -u | tr ' ' '_'); do
  name=${a//_/ }
  printf "%s: " "$name"; git log --author="$name" --name-only --pretty=format: | sort -u | grep -c . || true
done
