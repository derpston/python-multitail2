#!/bin/bash
set -e

cd src
pymodver=$(python -c 'import multitail2; print multitail2.__version__')
cd - >> /dev/null

packagever=$(head -1 debian/changelog | sed 's/[a-zA-Z0-9-]\+ (\([0-9.]\+\)).*/\1/g')

if [ "$pymodver" != "$packagever" ]
then
	echo "Version mismatch between debian/changelog ($packagever) and src/multitail2.py ($pymodver)"
	exit 1
fi


