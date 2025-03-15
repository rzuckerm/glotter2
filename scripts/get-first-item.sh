#!/bin/bash
echo "$1=$2" | sed 's/\s+//g' | cut -d',' -f1
