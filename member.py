from sys import argv
from app import stjb
from app import member as m
import os
import sys
from urllib.parse import urlparse

try:
    script, arg_member = argv
except ValueError:
    print('Missing argument')
    exit(-1)
db_uri = os.environ['CARDS_DATABASE_URI']
database = urlparse(db_uri).path
connection = stjb.connect(database)
member = m.find_members(connection, arg_member)
if member:
    #print(list(memberRow))
    m.load_member(connection, member)
    print(member.format_card())
else:
    print('Нет данных (not found)', file=sys.stderr)

