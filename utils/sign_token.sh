#!/bin/bash

echo -n $1 | kek sign -p | base64 | tr -d '\n'
echo
