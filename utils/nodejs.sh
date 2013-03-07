#!/usr/bin/env bash

# NODE.JS
# Installs Node.js.
# Based on http://community.webfaction.com/questions/4888/install-nodejs-with-express-framework

NODEVERSION="0.8.19"

mkdir -p $HOME/nodebuild
cd $HOME/nodebuild
wget 'http://nodejs.org/dist/v$NODEVERSION/node-v$NODEVERSION.tar.gz'
tar -xzf node-v$NODEVERSION.tar.gz
cd node-v$NODEVERSION

# All of these scripts use "#!/usr/bin/env python". Let's make that mean python2.7:
PATH_BACKUP="$PATH"
mkdir MYPY
ln -s $(which python2.7) $PWD/MYPY/python
export PATH="$PWD/MYPY:$PATH"

./configure --prefix=$HOME
make
make install

# restore the PATH (we don't need `$PWD/MYPY/python` anymore).
PATH="$PATH_BACKUP"

# Set the node modules path
export NODE_PATH="$HOME/lib/node_modules:$NODE_PATH"
echo 'export NODE_PATH="$HOME/lib/node_modules:$NODE_PATH"' >> $HOME/.bashrc

cd
rm -rf $HOME/nodebuild