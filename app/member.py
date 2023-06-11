from sys import argv
from . import stjb
import re
import os
import sys

class Member(stjb.AbstractMember):

    sql_members_by_name = """select * from Members_V C
            where C.Member_Last like :name OR
                  C.Member_First like :name OR
                  C.Member_First_Other like :name OR
                  C.Member_Middle like :name OR
                  C.Member_Maiden like :name OR
                  C.RU_Member_Last like :name OR
                  C.RU_Member_Maiden like :name OR
                  C.RU_Member_First like :name OR
                  C.RU_Member_Patronymic like :name
             order by Member_Last, Member_First"""

    sql_member_by_guid = "select * from Members_V where GUID = :guid"

    sql_payments_by_member = """select * from Payments_Dues
                where Member_Last like :lname AND
                      Member_First like :fname
                 order by Paid_From, Paid_Through"""

    def _format_name(self, member):
        ru_name = self.row[f'RU_{member}_Patronymic']
        ru_name = '' if ru_name is None else (' ' + ru_name)
        name = '%s, %s (%s, %s%s)' % (self.row[f'{member}_Last'], self.row[f'{member}_First'], self.row[f'RU_{member}_Last'], self.row[f'RU_{member}_First'], ru_name)
        return f'{name} †' if self.row[f'{member}_Status'] == 'Deceased' else name

    def format_name(self):
        return self._format_name('Member')

    def format_spouse_name(self):
        return self._format_name('Spouse')

    @property
    def member_from(self):
        return self.row['Member_From'] or stjb.DISTANT_PAST

    def historical_payments(self):
        historical_paid_thru = self.row['Dues_Paid_Through'] or stjb.DISTANT_PAST
        return [{
                'Date' : None,
                'Amount' : None,
                'Identifier' : None,
                'Method' : None,
                'Paid_From' : self.member_from,
                'Paid_Through' : historical_paid_thru,
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
        status = self['Member_Status']
        dues_amount = self['Dues_Amount']
        name = self.format_name()
        left.append(f'✼ {name}')
        right.append(f'{status}, ${dues_amount}')
        if self['Spouse_First'] and self['Spouse_Last']:
            spouse = self.format_spouse_name()
            left.append(f'  {spouse}')
            spouse_status = self['Spouse_Status']
            spouse_type = self['Spouse_Type']
            right.append(f'{spouse_type}, {spouse_status}')
        return stjb.format_two_columns(left, right, 59)

    def format_details_footer(self):
        left = []
        left.append(self['Address'])
        city = self['City']
        state = self['State_Region']
        postal_code = self['Postal_Code'] or ''
        plus4 = self['Plus_4']
        zip_code = postal_code + (f'-{plus4}' if plus4 else '')
        city_state_zip = f'{city}, {state} {zip_code}'
        left.append(city_state_zip)
        member_from = stjb.format_date(self['Member_from']) or '?'
        left.append('')
        left.append(f'Member from: {member_from}')

        right = []
        home_phone = self['Home_Phone']
        if home_phone:
            right.append(f'{home_phone} (home)')
        mobile_phone = self['Mobile_Phone']
        if mobile_phone:
            right.append(f'{mobile_phone} (mobile)')
        email_address = self['EMail_Address']
        if email_address:
            addresses = re.split(',|;| ', email_address)
            addresses = [addr for addr in addresses if addr != '']
            right = right + addresses
        return stjb.format_two_columns(left, right, 45)

    @property
    def fname(self):
        return self['Member_First']

    @property
    def lname(self):
        return self['Member_Last']

