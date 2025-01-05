from sys import argv
from . import stjb
import re
import os
import sys

class Member(stjb.AbstractMember):

    sql_members_by_name = """select * from member_v c
            where c.last_name like :name or
                  c.first_name like :name or
                  c.other_name like :name or
                  c.middle_name like :name or
                  c.maiden_name like :name or
                  c.ru_last_name like :name or
                  c.ru_maiden_name like :name or
                  c.ru_first_name like :name or
                  c.ru_patronymic_name like :name
             order by last_name, first_name"""

    sql_member_by_guid = "select * from member_v where guid = :guid"

    sql_payments_by_member = """select * from payment_sub_dues
                where last_name like :lname AND
                      first_name like :fname
                 order by paid_from, paid_through"""

    def _format_name(self, first, last, ru_first, ru_patronymic, ru_last, status):
        ru_name = ru_patronymic
        ru_name = '' if ru_name is None else (' ' + ru_name)
        name = '%s, %s (%s, %s%s)' % (last, first, ru_last, ru_first, ru_name)
        return f'{name} †' if status == 'Deceased' else name

    def format_name(self):
        return self._format_name(
            first=self['first_name'],
            last=self['last_name'],
            ru_first=self['ru_first_name'],
            ru_patronymic=self['ru_patronymic_name'],
            ru_last=self['ru_last_name'],
            status=self['member_status']
        )

    def format_spouse_name(self):
        return self._format_name(
            first=self['spouse_first_name'],
            last=self['spouse_last_name'],
            ru_first=self['ru_spouse_first_name'],
            ru_patronymic=self['ru_spouse_patronymic_name'],
            ru_last=self['ru_spouse_last_name'],
            status=self['spouse_status']
        )

    @property
    def member_from(self):
        return self['membership_from'] or stjb.DISTANT_PAST

    def historical_payments(self):
        historical_paid_thru = self['dues_paid_through'] or stjb.DISTANT_PAST
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
        status = self['member_status']
        dues_amount = self['dues_amount']
        name = self.format_name()
        left.append(f'✼ {name}')
        right.append(f'{status}, ${dues_amount}')
        if self['spouse_first_name'] and self['spouse_last_name']:
            spouse = self.format_spouse_name()
            left.append(f'  {spouse}')
            spouse_status = self['spouse_status']
            spouse_type = self['spouse_type']
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
        member_from = stjb.format_date(self['Membership_From']) or '?'
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
        return self['first_name']

    @property
    def lname(self):
        return self['last_name']

