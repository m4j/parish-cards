from sys import argv
from . import stjb
import re
from datetime import datetime
import os
import sys
from . import db
from .models import Prosphora

class Member(stjb.AbstractMember):

    model = Prosphora

    @classmethod
    def find_all_by_name(cls, name):
        selected = f'%{name}%'
        rows = db.session.scalars(
            db.select(Prosphora).filter(
                db.or_(
                    Prosphora.last_name.like(selected),
                    Prosphora.first_name.like(selected),
                    Prosphora.family_name.like(selected),
                    Prosphora.ru_last_name.like(selected),
                    Prosphora.ru_first_name.like(selected),
                    Prosphora.ru_family_name.like(selected),
                    Prosphora.notes.like(selected)
                )
            ).order_by(
                Prosphora.last_name, Prosphora.first_name
            )).all()
        return [cls(row) for row in rows]

    @property
    def fname(self):
        return self.row.first_name

    @property
    def lname(self):
        return self.row.last_name

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
        ru_fullname = self._format_name(self.row.ru_last_name, self.row.ru_first_name)
        en_fullname = self._format_name(self.row.last_name, self.row.first_name)
        return f'{en_fullname} ({ru_fullname})'

    @property
    def member_from(self):
        return stjb.DISTANT_PAST

    @property
    def member_through(self):
        return stjb.DISTANT_FUTURE

    def format_card(self):
        return (
            f'{self.format_details_header()}\n'
            f'{self.format_payments_table()}\n'
            f'{self.format_legend()}'
        )


    def format_details_header(self):
        name = self.format_name()
        quantity = self.row.quantity
        service = self.row.liturgy or 'Slavonic'
        comment = ''
        if len(self.row.payments) > 0:
            comment = '+12 Great Feasts' if self.row.payments[-1].with_twelve_feasts else ''
        comment = comment + (self.row.notes or '')
        comment = comment.strip()
        result = (
            f'✼ {name : <55}\n\n'
            f'  Liturgy: {service : <55}\n'
            f'  Quantity: {quantity : <55}\n'
            f'  {comment : <55}'
        )
        return result

