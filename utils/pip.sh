#!/usr/bin/env bash
set -e

# curl -O http://python-distribute.org/distribute_setup.py
curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py

for xy in 2.5 2.6 2.7; do
	mkdir -p $HOME/lib/python$xy
	python$xy get-pip.py
done

# for xy in 3.1 3.2 3.3; do
# 	mkdir -p $HOME/lib/python$xy
# 	python$xy distribute_setup.py --user
# 	python$xy get-pip.py
# done

# rm distribute_setup.py
rm get-pip.py