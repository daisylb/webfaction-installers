#!/usr/bin/env bash
set -e

# PIP
# Installs the Pip package manager for the following Python versions:
# 2.5 2.6 2.7 3.1 3.2 3.3
# (note lack of 2.4 and 3.0)

curl -O http://python-distribute.org/distribute_setup.py
curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py

for xy in 2.5 2.6 2.7; do
	mkdir -p $HOME/lib/python$xy
	python$xy get-pip.py
done

# On 3.x, the Pip installer tries to install it globally without this line
export PIP_INSTALL_OPTION="--user"

for xy in 3.1 3.2 3.3; do
	mkdir -p $HOME/lib/python$xy
	python$xy distribute_setup.py --user
	python$xy get-pip.py
done

rm distribute_setup.py
rm get-pip.py
rm distribute*.tar.gz