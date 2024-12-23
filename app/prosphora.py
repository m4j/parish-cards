from sys import argv
from . import stjb
import re
from datetime import datetime
import os
import sys

class Member(stjb.AbstractMember):

    sql_members_by_name = """select * from Prosphoras_V
                where EN_Surname like :name OR
                      EN_Name like :name OR
                      EN_Family like :name OR
                      RU_Surname like :name OR
                      RU_Name like :name OR
                      RU_Name_Patronymic like :name OR
                      RU_Family like :name
                 order by EN_Surname, EN_Name"""

    sql_member_by_guid = "select * from Prosphoras_V where GUID = :guid"

    sql_payments_by_member = """select * from payment_sub_prosphora
                where Surname = :lname AND (Name IS NULL OR Name = :fname)
                 order by Paid_From, Paid_Through"""

    @property
    def fname(self):
        return self['EN_Name']

    @property
    def lname(self):
        return self['EN_Surname']

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
        ru_fullname = self._format_name(self.row['RU_Surname'], self.row['RU_Name'], self.row['RU_Name_Patronymic'])
        en_fullname = self._format_name(self.row['EN_Surname'], self.row['EN_Name'], None)
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
        quantity = self['Quantity']
        service = self['Liturgy'] or 'Slavonic'
        comment = self['Comment'] or ''
        result = (
            f'✼ {name : <55}\n\n'
            f'  Liturgy: {service : <55}\n'
            f'  Quantity: {quantity : <55}\n'
            f'  {comment : <55}'
        )
        return result

