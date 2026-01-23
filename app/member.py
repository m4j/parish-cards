from sys import argv

from types import SimpleNamespace
from . import stjb
import re
import os
import sys
from . import db
from .models import Card

class Member(stjb.AbstractMember):

    model = Card

    @classmethod
    def find_all_by_name(cls, name):
        selected = f'%{name}%'
        rows = db.session.scalars(
            db.select(Card).filter(
                db.or_(
                    Card.last_name.like(selected),
                    Card.first_name.like(selected),
                    Card.other_name.like(selected),
                    Card.middle_name.like(selected),
                    Card.maiden_name.like(selected),
                    Card.ru_last_name.like(selected),
                    Card.ru_maiden_name.like(selected),
                    Card.ru_first_name.like(selected),
                    Card.ru_other_name.like(selected),
                    Card.ru_patronymic_name.like(selected)
                )
            ).order_by(
                Card.last_name, Card.first_name
            )).all()
        return [cls(row) for row in rows]

    def _format_name(self, first, last, ru_first, ru_patronymic, ru_last, status):
        ru_name = ru_patronymic
        ru_name = '' if ru_name is None else (' ' + ru_name)
        if ru_name:
            name = '%s, %s (%s, %s%s)' % (last, first, ru_last, ru_first, ru_name)
        else:
            name = '%s, %s' % (last, first)
        return f'{name} †' if status == 'Deceased' else name

    def format_name(self):
        return self._format_name(
            first=self.row.first_name,
            last=self.row.last_name,
            ru_first=self.row.ru_first_name,
            ru_patronymic=self.row.ru_patronymic_name,
            ru_last=self.row.ru_last_name,
            status=self.row.person.status
        )

    def format_spouse_name(self):
        spouse_card = self.row.person.spouse.card
        return self._format_name(
            first=self.row.person.spouse.first,
            last=self.row.person.spouse.last,
            ru_first=spouse_card.ru_first_name if spouse_card else None,
            ru_patronymic=spouse_card.ru_patronymic_name if spouse_card else None,
            ru_last=spouse_card.ru_last_name if spouse_card else None,
            status=self.row.person.spouse.status
        )

    @property
    def member_from(self):
        return self.row.membership_from or stjb.DISTANT_PAST

    def historical_payments(self):
        historical_paid_thru = self.row.dues_paid_through or stjb.DISTANT_PAST
        p_dict = {
                'date' : None,
                'amount' : None,
                'identifier' : None,
                'method' : None,
                'paid_from' : self.member_from,
                'paid_through' : historical_paid_thru,
                }
        return [SimpleNamespace(**p_dict)]

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
        status = self.row.person.status
        dues_amount = self.row.dues_amount
        name = self.format_name()
        left.append(f'✼ {name}')
        right.append(f'{status}, ${dues_amount}')
        if self.row.person.spouse:
            spouse = self.format_spouse_name()
            left.append(f'  {spouse}')
            spouse_status = self.row.person.spouse.status
            if not self.row.person.spouse.card:
                spouse_status = 'not a member'
            spouse_type = 'Wife' if self.row.person.gender == 'M' else 'Husband'
            right.append(f'{spouse_type}, {spouse_status}')
        return stjb.format_two_columns(left, right, 59)

    def format_details_footer(self):
        left = []
        left.append(self.row.person.address)
        city = self.row.person.city
        state = self.row.person.state_region
        postal_code = self.row.person.postal_code or ''
        plus4 = self.row.person.plus_4
        zip_code = postal_code + (f'-{plus4}' if plus4 else '')
        city_state_zip = f'{city}, {state} {zip_code}'
        left.append(city_state_zip)
        member_from = stjb.format_date(self.row.membership_from) or '?'
        left.append('')
        left.append(f'Member from: {member_from}')

        right = []
        home_phone = self.row.person.home_phone
        if home_phone:
            right.append(f'{home_phone} (home)')
        mobile_phone = self.row.person.mobile_phone
        if mobile_phone:
            right.append(f'{mobile_phone} (mobile)')
        email_address = self.row.person.email
        if email_address:
            addresses = re.split(',|;| ', email_address)
            addresses = [addr for addr in addresses if addr != '']
            right = right + addresses
        return stjb.format_two_columns(left, right, 45)

    @property
    def fname(self):
        return self.row.first_name

    @property
    def lname(self):
        return self.row.last_name

