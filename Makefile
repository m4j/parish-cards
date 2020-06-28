TOP := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
TARGET=poop_sheet
TARGET_DIR=target
VERSION=$(shell date '+%Y%m%d')
DISTR_DIR=output
DISTR_SHEET=$(DISTR_DIR)/$(TARGET)-$(VERSION).pdf
DATABASE=../StJohnDC.db

MERGE=src/merge.py
#LATEX=pdflatex -output-directory=$(TARGET_DIR)
#LATEX=pdflatex -halt-on-error
LATEX=xelatex -halt-on-error
PDFTK=pdftk

UNAME=$(shell uname)
ifeq ($(UNAME), Linux)
	SED_INPLACE=sed -i
endif
ifeq ($(UNAME), Darwin)
	SED_INPLACE=sed -i ''
endif

.PHONY: all clean distr sheet import
.PRECIOUS: %.csv %.tex

all: distr

distr: $(DISTR_DIR) sheet 

sheet: $(DISTR_DIR) $(DISTR_SHEET)

$(DISTR_DIR):
	mkdir -p $@

$(DISTR_SHEET): $(TARGET).pdf
	cp $< $@

%.pdf: %.tex
	$(LATEX) $<
	latex_count=5 ; \
	while egrep -s 'Rerun (LaTeX|to get (cross-references|outlines) right)' $(*F).log && [ $$latex_count -gt 0 ] ;\
		do \
		  echo "Rerunning latex...." ;\
		  $(LATEX) $< ;\
		  latex_count=`expr $$latex_count - 1` ;\
		done

%.tex: src/%.tex %.csv 
	$(MERGE) $^ > $@

%.csv: $(DATABASE) 
	sqlite3 $< -csv -header 'select * from Payments_Sheet where Date = "$(VERSION)";' > $@

import: import_MemberList import_FamilyList $(DATABASE)

import_%: src/%.csv $(DATABASE)
	sqlite3 -echo $(DATABASE) 'DROP TABLE IF EXISTS ParishSoft_$*;'
	sqlite3 -echo -csv $(DATABASE) '.import $< ParishSoft_$*'

clean:
	rm -f $(TARGET)*
