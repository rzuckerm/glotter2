#!/bin/bash
echo "$1=[$2]" | sed -r 's/([0-9.]+)/"\1"/g'
