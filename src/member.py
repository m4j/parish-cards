from sys import argv
import stjb
import re
from datetime import datetime
import os
import sys

SQL_MEMBER_BY_NAME = """select * from Members_V C
            where C.[Member Last] like :name OR
                  C.[Member First] like :name OR
                  C.[Member First Other] like :name OR
                  C.[Member Middle] like :name OR
                  C.[Member Maiden] like :name OR
                  C.[RU Member Last] like :name OR
                  C.[RU Member Maiden] like :name OR
                  C.[RU Member First] like :name OR
                  C.[RU Member Patronymic] like :name
             order by [Member Last], [Member First]"""

SQL_PAYMENTS_BY_MEMBER = """select * from Payments_Dues
            where [Member Last] like :lname AND
                  [Member First] like :fname
             order by [Paid From], [Paid Through]"""

class Member(stjb.AbstractMember):

    def _format_name(self, member):
        ru_name = self.row[f'RU {member} Patronymic']
        ru_name = '' if ru_name is None else (' ' + ru_name)
        name = '%s, %s%s (%s, %s)' % (self.row[f'RU {member} Last'], self.row[f'RU {member} First'], ru_name, self.row[f'{member} Last'], self.row[f'{member} First'])
        return f'{name} †' if self.row[f'{member} Status'] == 'Deceased' else name

    def format_name(self):
        return self._format_name('Member')

    def format_spouse_name(self):
        return self._format_name('Spouse')

    @property
    def member_from(self):
        return self.row['Member From'] or stjb.DISTANT_PAST

    def historical_payments(self):
        historical_paid_thru = self.row['Dues Paid Through'] or stjb.DISTANT_PAST
        return [{
                'Date' : None,
                'Amount' : None,
                'Identifier' : None,
                'Method' : None,
                'Paid From' : self.member_from,
                'Paid Through' : historical_paid_thru,
                }]


def format_member_details(row):
    status = row['Member Status']
    spouse_status = ''
    name = row.format_name()
    spouse = ''
    if row['Spouse First'] and row['Spouse Last']:
        spouse = row.format_spouse_name()
        spouse_status = row['Spouse Status']
        spouse_type = row['Spouse Type']
        spouse_status = f'{spouse_type}, {spouse_status}'
    dues_amount = row['Dues Amount']
    member_from = format_date(row['Member From']) or '?'
    address = row['Address']
    city = row['City']
    state = row['State/Region']
    postal_code = row['Postal Code']
    plus4 = row['Plus 4']
    zip_code = postal_code + (f'-{plus4}' if plus4 else '')
    city_state_zip = f'{city}, {state} {zip_code}'
    email = row['E-Mail Address']
    phones = []
    home_phone = row['Home Phone']
    if home_phone:
        phones.append(f'{home_phone} (home)')
    mobile_phone = row['Mobile Phone']
    if mobile_phone:
        phones.append(f'{mobile_phone} (mobile)')
    work_phone = row['Work Phone']
    if work_phone: 
        phones.append(f'{work_phone} (work)')
    phones_line = ', '.join(phones)
    member_from = format_date(row['Member from']) or '?'

    result = (
        f'✼ {name : <55}{status}\n'
        f'  {spouse : <55}{spouse_status}\n'
        f'{address : <57}Monthly dues: ${dues_amount}\n'
        f'{city_state_zip : <57}Member from {member_from}\n'
        f'{phones_line}'
    )
    if email:
        result = f'{result}\n{email}'
    return result

def find_member(member, picker=stjb.pick_by_index):
    selected = member + '%'
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
        'fname': member['Member First'],
        'lname': member['Member Last'],
    }
    cursor.execute(SQL_PAYMENTS_BY_MEMBER, query_parameters)
    return cursor.fetchall()

def format_date(date):
    split = date.split('-') if date else []
    if len(split) >= 2:
        year = split[0]
        month = stjb.MONTHS_DICT[split[1]]
        return f'{month} {year}'
    else:
        return None

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

