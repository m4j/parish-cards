TOP := .
PAYMENTS=poop_sheet
PROSPHORAS=prosphoras
VERSION=9999-12-31
DISTR_DIR=$(TOP)/output
DISTR_PAYMENTS=$(DISTR_DIR)/$(PAYMENTS)-$(VERSION).pdf
DISTR_PROSPHORAS=$(DISTR_DIR)/$(PROSPHORAS)-$(VERSION).pdf
DATABASE=$(TOP)/../StJohnDC.db
DATABASE_DIR=$(TOP)/database
APP_DIR=$(TOP)/app
TEMPLATES_DIR=$(APP_DIR)/templates

MERGE=$(APP_DIR)/merge.py
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

all: distr

distr: $(DISTR_DIR) payments

payments: $(DISTR_DIR) $(DISTR_PAYMENTS)

prosphoras: prosphoranotes.tex $(DISTR_DIR) $(DISTR_PROSPHORAS)

prosphoranotes.tex: $(TEMPLATES_DIR)/prosphoranotes.tex
	cp $< $@

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

$(PROSPHORAS).tex: $(PROSPHORAS).csv
	$(MERGE) $@ $< > $@

$(PAYMENTS).tex: $(PAYMENTS).csv
	$(MERGE) $@ $< > $@

$(PAYMENTS).csv: $(DATABASE)
	sqlite3 $< -csv -header 'select * from payment_sheet_v where record_id like "$(VERSION)";' > $@

$(PROSPHORAS).csv: $(DATABASE)
	sqlite3 $< -csv -header 'select * from prosphora_current_v order by name;' > $@

import: import_MemberList import_FamilyList $(DATABASE)

import_%: $(DATABASE_DIR)/%.csv $(DATABASE)
	sqlite3 -echo $(DATABASE) 'DROP TABLE IF EXISTS ParishSoft_$*;'
	sqlite3 -echo -csv $(DATABASE) '.import $< ParishSoft_$*'

clean:
	rm -f $(PAYMENTS)* $(PROSPHORAS)*
