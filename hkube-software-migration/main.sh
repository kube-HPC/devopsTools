#!/bin/bash

if [ -z "${OS}" ]
then
    echo 'found linux OS , start process....'
    ./scripts/compile.sh $1
else
    echo 'no support on windows OS system'
fi