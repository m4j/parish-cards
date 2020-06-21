#!/usr/bin/env python3

import os
import jinja2

jinja_env = jinja2.Environment(
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
    loader=jinja2.FileSystemLoader(os.getcwd()))

class LaTexReader:

    def __init__(self, reader):
        self.reader = reader

    def __next__(self):
        row = next(self.reader)
        return self.escape_special_characters(row)

    def __iter__(self):
        return self

    def escape_special_characters(self, el_str):
        s = el_str.replace('<', '$<$')
        s = s.replace('>', '$>$')
        s = s.replace(' - ', u' — ')
        s = s.replace('#', '\\#')
        s = s.replace('_', '\\_')
        s = s.replace('&', '\\&')
        s = s.replace('\r\n', '\n\n')
        return s

