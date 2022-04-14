from sys import argv
import stjb
import re
from datetime import datetime
import os
import sys

SQL_MEMBER_BY_NAME = """select * from Prosphoras_V
            where [EN Surname] like :name OR
                  [EN Name] like :name OR
                  [EN Family] like :name OR
                  [RU Surname] like :name OR
                  [RU Name] like :name OR
                  [RU Name Patronymic] like :name OR
                  [RU Family] like :name
             order by [EN Surname], [EN Name]"""

SQL_PAYMENTS_BY_MEMBER = """select * from Payments_Prosphoras
            where Surname = :lname AND (Name IS NULL OR Name = :fname)
             order by [Paid From], [Paid Through]"""

class Member(stjb.AbstractMember):

    def _format_name(self, surname, name, patronymic = None):
        names = []
        if surname:
            names.append(surname)
        if name:
            names.append(name)
        if len(names) > 0:
            names[0] = names[0].upper()
        fullname = ', '.join(names)
        if patronymic:
            fullname = f'{fullname} {patronymic}'
        return fullname

    def format_name(self):
        ru_fullname = self._format_name(self.row['RU Surname'], self.row['RU Name'], self.row['RU Name Patronymic'])
        en_fullname = self._format_name(self.row['EN Surname'], self.row['EN Name'], None)
        return f'{en_fullname} ({ru_fullname})'

    @property
    def member_from(self):
        return stjb.DISTANT_PAST


def format_member_details(row):
    name = row.format_name()
    quantity = row['Quantity']
    service = row['Liturgy'] or 'Slavonic'
    comment = row['Comment'] or ''
    result = (
        f'✼ {name : <55}\n\n'
        f'  Liturgy: {service : <55}\n'
        f'  Quantity: {quantity : <55}\n'
        f'  {comment : <55}'
    )
    return result

def find_member(member, picker=stjb.pick_by_index):
    selected = '%' + member + '%'
    cursor = conn.cursor()
    cursor.execute(SQL_MEMBER_BY_NAME, {'name': selected})
    rows = cursor.fetchall()
    members = list(map(Member, rows))
    formatted = list(map(Member.format_name, members))
    index = picker(formatted)
    return None if index is None else members[index]

def find_payments(member):
    cursor = conn.cursor()
    query_parameters = {
        'fname': member['EN Name'],
        'lname': member['EN Surname'],
    }
    cursor.execute(SQL_PAYMENTS_BY_MEMBER, query_parameters)
    return cursor.fetchall()

try:
    script, arg_member = argv
except ValueError:
    print('Missing argument')
    exit(-1)
database = os.environ['STJB_DATABASE']
conn = stjb.connect(database)
member = find_member(arg_member)
if member:
    #print(list(memberRow))
    member.payments = find_payments(member)
    print(format_member_details(member))
    stjb.print_payments_table(member)
else:
    print('Нет данных (not found)', file=sys.stderr)

