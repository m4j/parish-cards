#!/usr/bin/env python3

from sys import argv
import csv
from latex import LaTexReader, jinja_env
import re

script, arg_template, arg_data = argv

def markdown_to_latex(row, key):
    result = row.copy()
    if key in result:
        string = result[key]
        string = re.sub(r"\*\*(.*)\*\*", r"\\textbf{\1}", string)
        result[key] = string
    return result

with open(arg_data, encoding='utf-8', newline='') as csvfile:
    latexReader = LaTexReader(csvfile)
    reader = list(csv.DictReader(latexReader))
    #for row in reader:
        #print(row)
    reader = list(map(lambda r: markdown_to_latex(r, "purpose"), reader))
    template = jinja_env.get_template(arg_template)
    rendered_tex = template.render(data=reader)
    print(rendered_tex)

