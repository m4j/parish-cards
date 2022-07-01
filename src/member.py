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

def format_member_details_header(row):
    left = []
    right = []
    status = row['Member Status']
    dues_amount = row['Dues Amount']
    name = row.format_name()
    left.append(f'✼ {name}')
    right.append(f'{status}, ${dues_amount}')
    if row['Spouse First'] and row['Spouse Last']:
        spouse = row.format_spouse_name()
        left.append(f'  {spouse}')
        spouse_status = row['Spouse Status']
        spouse_type = row['Spouse Type']
        right.append(f'{spouse_type}, {spouse_status}')
    return stjb.format_two_columns(left, right, 55)

def format_member_details_footer(row):
    left = []
    left.append(row['Address'])
    city = row['City']
    state = row['State/Region']
    postal_code = row['Postal Code']
    plus4 = row['Plus 4']
    zip_code = postal_code + (f'-{plus4}' if plus4 else '')
    city_state_zip = f'{city}, {state} {zip_code}'
    left.append(city_state_zip)
    member_from = stjb.format_date(row['Member from']) or '?'
    left.append('-----')
    left.append(f'Member from: {member_from}')

    right = []
    home_phone = row['Home Phone']
    if home_phone:
        right.append(f'{home_phone} (home)')
    mobile_phone = row['Mobile Phone']
    if mobile_phone:
        right.append(f'{mobile_phone} (mobile)')
    work_phone = row['Work Phone']
    if work_phone: 
        right.append(f'{work_phone} (work)')
    email_address = row['E-Mail Address']
    if email_address:
        addresses = re.split(',|;| ', email_address)
        addresses = [addr for addr in addresses if addr != '']
        right = right + addresses
    return stjb.format_two_columns(left, right, 45)

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
    print(format_member_details_header(member))
    stjb.print_payments_table(member)
    print(format_member_details_footer(member))
else:
    print('Нет данных (not found)', file=sys.stderr)

