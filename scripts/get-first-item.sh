#!/bin/bash
# arguments: <variable_name> <string>
echo "$1=$2" | sed 's/\s+//g' | cut -d',' -f1
