#!/bin/bash

if [ -z "${OS}" ]
then
    echo 'found linux OS , start process....'
    ./scripts/linux_compile.sh $1
else
    echo 'found Windows OS , start process....'
    ./scripts/windows_compile.py
fi