from sys import argv
import html as html_module
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
                    Card.ru_patronymic_name.like(selected),
                    Card.notes.like(selected),
                    Card.membership_termination_reason.like(selected)
                )
            ).order_by(
                Card.last_name, Card.first_name
            )).all()
        return [cls(row) for row in rows]

    def _format_name(self, first, last, ru_first, ru_patronymic, ru_last, status):
        name = f'{last}, {first}'
        if ru_first and ru_last:
            ru_name = f'{ru_first} {ru_patronymic}' if ru_patronymic else ru_first
            name = f'{name} ({ru_last}, {ru_name})'
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

    @property
    def member_through(self):
        return self.row.membership_through or stjb.DISTANT_FUTURE

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

    def format_html_card(self):
        return (
            '<div class="card-container">'
            f'{self.format_html_details_header()}'
            f'{self.format_html_payments_table()}'
            f'{self.format_html_details_footer()}'
            f'{self.format_html_legend()}'
            '</div>'
        )

    def format_details_header(self):
        left = []
        right = []
        status = 'former member' if self.row.membership_through else 'member'
        dues_amount = self.row.dues_amount
        left.append(f'{self.format_member_term()}')
        right.append(f'${dues_amount}')
        if self.row.person.spouse:
            spouse = self.format_spouse_name()
            spouse_term = 'Wife' if self.row.person.gender == 'M' else 'Husband'
            left.append(f'{spouse_term}: {spouse}')
            spouse_status = 'not a member'
            if self.row.person.spouse.card:
                spouse_status = 'former member' if self.row.person.spouse.card.membership_through else 'member'
                spouse_status = f'{spouse_status} ${self.row.person.spouse.card.dues_amount}'
            right.append(f'{spouse_status}')
        return stjb.format_two_columns(left, right, 64)

    def format_html_details_header(self):
        def esc(s):
            return html_module.escape(str(s))
        rows = []
        dues_amount = self.row.dues_amount
        rows.append((f'{self.format_member_term()}', f'${dues_amount}'))
        if self.row.person.spouse:
            spouse = self.format_spouse_name()
            spouse_term = 'Wife' if self.row.person.gender == 'M' else 'Husband'
            spouse_status = 'not a member'
            if self.row.person.spouse.card:
                spouse_status = 'former member' if self.row.person.spouse.card.membership_through else 'member'
                spouse_status = f'{spouse_status} ${self.row.person.spouse.card.dues_amount}'
            rows.append((f'{spouse_term}: {spouse}', spouse_status))
        parts = ['<table class="card-details-header">']
        for left, right in rows:
            parts.append(f'<tr><td class="details-left">{esc(left)}</td><td class="details-right">{esc(right)}</td></tr>')
        parts.append('</table>')
        return ''.join(parts)

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
        left.append('')

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

    def format_member_term(self):
        member_from = stjb.format_date(self.row.membership_from) or '?'
        member_through = stjb.format_date(self.row.membership_through)
        status = 'Former member' if self.row.membership_through else 'Member'
        member_term = f'{status} from {member_from}'
        if member_through:
            member_term = f'{member_term} – {member_through}'
            if self.row.membership_termination_reason:
                member_term = f'{member_term} ({self.row.membership_termination_reason})'
        return member_term

    def format_html_details_footer(self):
        def esc(s):
            return html_module.escape(str(s))
        left_rows = []
        left_rows.append(self.row.person.address or '')
        city = self.row.person.city or ''
        state = self.row.person.state_region or ''
        postal_code = self.row.person.postal_code or ''
        plus4 = self.row.person.plus_4
        zip_code = postal_code + (f'-{plus4}' if plus4 else '')
        city_state_zip = f'{city}, {state} {zip_code}'.strip(', ')
        left_rows.append(city_state_zip)
        left_rows.append('')
        right_rows = []
        if self.row.person.home_phone:
            right_rows.append(f'{self.row.person.home_phone} (home)')
        if self.row.person.mobile_phone:
            right_rows.append(f'{self.row.person.mobile_phone} (mobile)')
        if self.row.person.email:
            addresses = re.split(r'[,; ]', self.row.person.email)
            right_rows.extend(addr for addr in addresses if addr)
        max_rows = max(len(left_rows), len(right_rows))
        parts = ['<table class="card-details-footer">']
        for i in range(max_rows):
            left = left_rows[i] if i < len(left_rows) else ''
            right = right_rows[i] if i < len(right_rows) else ''
            parts.append(f'<tr><td class="details-left">{esc(left)}</td><td class="details-right">{esc(right)}</td></tr>')
        parts.append('</table>')
        return ''.join(parts)

    @property
    def fname(self):
        return self.row.first_name

    @property
    def lname(self):
        return self.row.last_name

