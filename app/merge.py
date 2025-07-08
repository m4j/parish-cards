#!/usr/bin/env python3

from sys import argv
import csv
from latex import jinja_latex_env, md_to_latex, escape_special_latex_characters
import re

script, arg_template, arg_data = argv

class LaTexReader:

    def __init__(self, reader):
        self.reader = reader
        self.dont_escape_header = True

    def __next__(self):
        row = next(self.reader)
        if self.dont_escape_header:
            self.dont_escape_header = False
            return row
        else:
            return escape_special_latex_characters(row)

    def __iter__(self):
        return self

def markdown_to_latex(row, key):
    result = row.copy()
    if key in result:
        string = result[key]
        result[key] = md_to_latex(string)
    return result

with open(arg_data, encoding='utf-8', newline='') as csvfile:
    latexReader = LaTexReader(csvfile)
    reader = list(csv.DictReader(latexReader))
    #for row in reader:
        #print(row)
    reader = list(map(lambda r: markdown_to_latex(r, "purpose"), reader))
    template = jinja_latex_env.get_template(arg_template)
    rendered_tex = template.render(data=reader)
    print(rendered_tex)

