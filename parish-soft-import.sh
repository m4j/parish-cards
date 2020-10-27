#!/bin/sh

for csv in MemberList.csv FamilyList.csv; do (cat ~/Downloads/$csv | dos2unix | (read -r; printf "%s\n" "$REPLY"; sort) > src/$csv) && rm ~/Downloads/$csv; done && make import

