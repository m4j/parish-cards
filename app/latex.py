#!/usr/bin/env python3

import os
import jinja2
from pytracetoix import c__, d__
import re

jinja_latex_env = jinja2.Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    #loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    #loader=jinja2.FileSystemLoader(os.getcwd()))
    loader=jinja2.PackageLoader(__name__, 'templates')
)

jinja_latex_env.globals['c__'] = c__
jinja_latex_env.globals['d__'] = d__

def escape_special_latex_characters(el_str):
    if isinstance(el_str, dict):
        return {k: escape_special_latex_characters(v) for k, v in el_str.items()}
    if isinstance(el_str, str):
        s = el_str.replace('$', '\\$')
        s = s.replace('<', '$<$')
        s = s.replace('>', '$>$')
        s = s.replace('#', '\\#')
        s = s.replace('_', '\\_')
        s = s.replace('&', '\\&')
        s = s.replace('\r\n', '\n\n')
        return s
    return el_str

def md_to_latex(string):
    string = re.sub(r"\*\*(.*)\*\*", r"\\textbf{\1}", string)
    return string
