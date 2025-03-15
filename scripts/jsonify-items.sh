#!/bin/bash
# arguments: <variable_name> <string> <regex_value_chars>
echo "$1=[$(echo "$2" | sed -r 's/(['"$3"']+)/"\1"/g')]"
