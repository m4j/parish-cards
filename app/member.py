from sys import argv
from . import stjb
import re
import os
import sys

class Member(stjb.AbstractMember):

    sql_members_by_name = """select * from Members_V C
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

    sql_member_by_guid = "select * from Members_V where GUID = :guid"

    sql_payments_by_member = """select * from Payments_Dues
                where [Member Last] like :lname AND
                      [Member First] like :fname
                 order by [Paid From], [Paid Through]"""

    def _format_name(self, member):
        ru_name = self.row[f'RU {member} Patronymic']
        ru_name = '' if ru_name is None else (' ' + ru_name)
        name = '%s, %s (%s, %s%s)' % (self.row[f'{member} Last'], self.row[f'{member} First'], self.row[f'RU {member} Last'], self.row[f'RU {member} First'], ru_name)
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

    def format_card(self):
        return (
            f'{self.format_details_header()}\n'
            f'{self.format_payments_table()}\n'
            f'{self.format_details_footer()}\n'
            f'{self.format_legend()}'
        )

    def format_details_header(self):
        left = []
        right = []
        status = self['Member Status']
        dues_amount = self['Dues Amount']
        name = self.format_name()
        left.append(f'✼ {name}')
        right.append(f'{status}, ${dues_amount}')
        if self['Spouse First'] and self['Spouse Last']:
            spouse = self.format_spouse_name()
            left.append(f'  {spouse}')
            spouse_status = self['Spouse Status']
            spouse_type = self['Spouse Type']
            right.append(f'{spouse_type}, {spouse_status}')
        return stjb.format_two_columns(left, right, 59)

    def format_details_footer(self):
        left = []
        left.append(self['Address'])
        city = self['City']
        state = self['State/Region']
        postal_code = self['Postal Code'] or ''
        plus4 = self['Plus 4']
        zip_code = postal_code + (f'-{plus4}' if plus4 else '')
        city_state_zip = f'{city}, {state} {zip_code}'
        left.append(city_state_zip)
        member_from = stjb.format_date(self['Member from']) or '?'
        left.append('')
        left.append(f'Member from: {member_from}')

        right = []
        home_phone = self['Home Phone']
        if home_phone:
            right.append(f'{home_phone} (home)')
        mobile_phone = self['Mobile Phone']
        if mobile_phone:
            right.append(f'{mobile_phone} (mobile)')
        work_phone = self['Work Phone']
        if work_phone: 
            right.append(f'{work_phone} (work)')
        email_address = self['E-Mail Address']
        if email_address:
            addresses = re.split(',|;| ', email_address)
            addresses = [addr for addr in addresses if addr != '']
            right = right + addresses
        return stjb.format_two_columns(left, right, 45)

    @property
    def fname(self):
        return self['Member First']

    @property
    def lname(self):
        return self['Member Last']

