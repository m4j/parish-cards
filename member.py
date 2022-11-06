from sys import argv
from app import stjb
from app import member as m
import os
import sys

try:
    script, arg_member = argv
except ValueError:
    print('Missing argument')
    exit(-1)
database = os.environ['STJB_DATABASE']
connection = stjb.connect(database)
member = m.find_members(connection, arg_member)
if member:
    #print(list(memberRow))
    m.load_member(connection, member)
    print(member.format_card())
else:
    print('Нет данных (not found)', file=sys.stderr)

