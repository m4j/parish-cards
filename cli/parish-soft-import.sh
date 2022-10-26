#!/bin/sh

export DATABASE_DIR=database

for csv in MemberList.csv FamilyList.csv; do (cat ~/Downloads/$csv | dos2unix | (read -r; printf "%s\n" "$REPLY"; sort) > $DATABASE_DIR/$csv) && rm ~/Downloads/$csv; done && make import

