#!/usr/bin/env python3

from sys import argv
import csv
from latex import LaTexReader, jinja_env

script, arg_template, arg_data = argv

with open(arg_data, encoding='utf-8', newline='') as csvfile:
    latexReader = LaTexReader(csvfile)
    reader = csv.DictReader(latexReader)
    #for row in reader:
        #print(row)
    template = jinja_env.get_template(arg_template)
    rendered_tex = template.render(data=reader)
    print(rendered_tex)

