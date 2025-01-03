from sys import argv
from . import stjb
import re
from datetime import datetime
import os
import sys

class Member(stjb.AbstractMember):

    sql_members_by_name = """select * from prosphoras_v
                where en_last_name like :name or
                      en_name like :name or
                      en_family_name like :name or
                      ru_last_name like :name or
                      ru_first_name like :name or
                      ru_family_name like :name
                 order by en_last_name, en_name"""

    sql_member_by_guid = "select * from prosphoras_v where guid = :guid"

    sql_payments_by_member = """select * from payment_sub_prosphora
                where last_name = :lname and (name is null or name = :fname)
                 order by paid_from, paid_through"""

    @property
    def fname(self):
        return self['en_name']

    @property
    def lname(self):
        return self['en_last_name']

    def _format_name(self, last_name, name, patronymic = None):
        names = []
        if last_name:
            names.append(last_name)
        if name:
            names.append(name)
        if len(names) > 0:
            names[0] = names[0].upper()
        fullname = ', '.join(names)
        if patronymic:
            fullname = f'{fullname} {patronymic}'
        return fullname

    def format_name(self):
        ru_fullname = self._format_name(self['ru_last_name'], self.row['ru_first_name'])
        en_fullname = self._format_name(self['en_last_name'], self.row['en_name'])
        return f'{en_fullname} ({ru_fullname})'

    @property
    def member_from(self):
        return stjb.DISTANT_PAST

    def format_card(self):
        return (
            f'{self.format_details_header()}\n'
            f'{self.format_payments_table()}\n'
            f'{self.format_legend()}'
        )


    def format_details_header(self):
        name = self.format_name()
        quantity = self['quantity']
        service = self['liturgy'] or 'Slavonic'
        comment = self['comment'] or ''
        result = (
            f'✼ {name : <55}\n\n'
            f'  Liturgy: {service : <55}\n'
            f'  Quantity: {quantity : <55}\n'
            f'  {comment : <55}'
        )
        return result

