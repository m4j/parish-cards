TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PAYMENTS=poop_sheet
PROSPHORAS=prosphoras
VERSION=$(shell date '+%Y%m%d')
DISTR_DIR=output
DISTR_PAYMENTS=$(DISTR_DIR)/$(PAYMENTS)-$(VERSION).pdf
DISTR_PROSPHORAS=$(DISTR_DIR)/$(PROSPHORAS)-$(VERSION).pdf
DATABASE=../StJohnDC.db

MERGE=src/merge.py
#LATEX=pdflatex -output-directory=$(PAYMENTS_DIR)
#LATEX=pdflatex -halt-on-error
LATEX=xelatex -halt-on-error

UNAME=$(shell uname)
ifeq ($(UNAME), Linux)
	SED_INPLACE=sed -i
    HASH=md5sum
endif
ifeq ($(UNAME), Darwin)
	SED_INPLACE=sed -i ''
    HASH=md5 -q
endif

.PHONY: all clean distr payments import
.PRECIOUS: %.csv %.tex

all: distr

distr: $(DISTR_DIR) payments 

payments: $(DISTR_DIR) $(DISTR_PAYMENTS)

prosphoras: $(DISTR_DIR) $(DISTR_PROSPHORAS)

$(DISTR_DIR):
	mkdir -p $@

$(DISTR_PAYMENTS): $(PAYMENTS).pdf
	cp $< $@

$(DISTR_PROSPHORAS): $(PROSPHORAS).pdf
	cp $< $@

%.pdf: %.tex
	aux_hash_prev="zzz" ; \
	aux_hash=`$(HASH) $(*F).aux 2>/dev/null` ;\
	while [ "$$aux_hash" != "$$aux_hash_prev" ];\
		do \
          aux_hash_prev=$$aux_hash ;\
		  echo "Rerunning latex....$$aux_hash" ;\
		  $(LATEX) $< ;\
          aux_hash=`$(HASH) $(*F).aux 2>/dev/null` ;\
		done

%.tex: src/%.tex %.csv 
	$(MERGE) $^ > $@

$(PAYMENTS).csv: $(DATABASE)
	sqlite3 $< -csv -header 'select * from Payments_Sheet where Date = "$(VERSION)";' > $@

$(PROSPHORAS).csv: $(DATABASE)
	sqlite3 $< -csv -header 'select * from Prosphoras_V order by Name;' > $@

import: import_MemberList import_FamilyList $(DATABASE)

import_%: src/%.csv $(DATABASE)
	sqlite3 -echo $(DATABASE) 'DROP TABLE IF EXISTS ParishSoft_$*;'
	sqlite3 -echo -csv $(DATABASE) '.import $< ParishSoft_$*'

clean:
	rm -f $(PAYMENTS)* $(PROSPHORAS)*
