import decimal
import html as html_module
from abc import ABC, abstractmethod
from functools import reduce
from . import db
from .models import PaymentMethod, PaymentSubMiscCategory
import uuid
from collections import namedtuple

DISTANT_PAST = '1970-01'
DISTANT_FUTURE = '9999-12'
FIRST_FROM = '2022-01'
LAST_THRU = '2027-12'
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
MONTH_NUMBERS = ['01','02','03','04','05','06','07','08','09','10','11','12']
MONTHS_DICT = { number : MONTHS[int(number)-1] for number in MONTH_NUMBERS }
TABLE_CELL_WIDTH = 13

Cell = namedtuple('Cell', ['text', 'cls'])

NON_MEMBER_CELL = Cell(f'{"" :░<{TABLE_CELL_WIDTH}}', 'non-member')
ARCHIVE_CELL = Cell('...', 'archive')
JAN_CONTINUITY_CELL = Cell('─╮ ', 'jan-continuity')
DEC_CONTINUITY_CELL = Cell('      ╰─▶    ', 'dec-continuity')
CONTINUITY_CELL = Cell('│', 'continuity')
DOWN_ARROW_CELL = Cell('▼', 'continuity end-of-range')

class AbstractMember(ABC):

    model = None

    def __init__(self, row):
        self.row = row
        self.payments = row.payments
        self.payment_methods = load_payment_methods()

    @classmethod
    @abstractmethod
    def find_all_by_name(cls, name):
        pass

    @classmethod
    def find_by_guid(cls, guid):
        row = db.session.execute(
            db.select(cls.model).filter_by(guid=uuid.UUID(guid))
        ).scalar()
        return None if row is None else cls(row)

    @property
    def guid(self):
        return self.row.guid

    @property
    @abstractmethod
    def fname(self):
        pass

    @property
    @abstractmethod
    def lname(self):
        pass

    @abstractmethod
    def format_name(self):
        pass

    def __getitem__(self, key):
        return self.row[key]

    @property
    @abstractmethod
    def member_from(self):
        pass

    @property
    @abstractmethod
    def member_through(self):
        pass

    def historical_payments(self):
        return []

    @abstractmethod
    def format_card(self):
        pass

    def paid_through_month(self):
        all_payments = self.historical_payments() + self.payments
        l = len(all_payments)
        if l == 0:
            return None
        last = all_payments[l-1]
        last_paid_through = last.paid_through
        month = last_paid_through.split('-')[1]
        return MONTHS_DICT[month]

    def format_payments_table(self):
        buffer = ''
        first_year = int(FIRST_FROM.split('-')[0])
        last_year = int(LAST_THRU.split('-')[0])
        buffer += format_header(range(first_year, last_year + 1)) + '\n'
        year_totals = list(map(lambda y: 0, range(first_year, last_year + 1)))
        paid_through_m = self.paid_through_month()
        for i, month in enumerate(MONTHS):
            row1 = f' {month} *' if month == paid_through_m else f' {month}  '
            row2 = '      '
            month_number = MONTH_NUMBERS[i]
            for j, year in enumerate(range(first_year, last_year + 1)):
                cells = self.format_payment_cells_for(year, month_number)
                payments_this_month = cells[2]
                if payments_this_month:
                    year_totals[j] = year_totals[j] + payments_this_month
                def fit(s, w=TABLE_CELL_WIDTH):
                    return (s[: w - 3] + '...') if len(s) > w else s
                cell1 = f'{fit(cells[0].text):^{TABLE_CELL_WIDTH}}'
                cell2 = f'{fit(cells[1].text):^{TABLE_CELL_WIDTH}}'
                payments_date = f'{year}-{month_number}'
                if payments_date < self.member_from or payments_date > self.member_through:
                    cell1 = cell1.replace(' ', '░')
                    cell2 = cell2.replace(' ', '░')
                row1 = f'{row1}{cell1} '
                row2 = f'{row2}{cell2} '
            buffer += row1 + '\n'
            buffer += row2 + '\n'
        formatted_year_totals = list(map(lambda t: f'${round(t, 2)}' if t else '', year_totals))
        buffer += format_footer(formatted_year_totals)
        return buffer

    def format_html_payments_table(self):
        first_year = int(FIRST_FROM.split('-')[0])
        last_year = int(LAST_THRU.split('-')[0])
        years = list(range(first_year, last_year + 1))
        year_totals = [0] * len(years)
        paid_through_m = self.paid_through_month()

        def esc(s):
            return html_module.escape(str(s))

        parts = ['<table class="payments-table">']
        # Header row: empty corner + year headers
        parts.append('<thead><tr><th></th>')
        for y in years:
            parts.append(f'<th class="year">{esc(y)}</th>')
        parts.append('</tr></thead><tbody>')

        for i, month in enumerate(MONTHS):
            month_number = MONTH_NUMBERS[i]
            is_paid_through = month == paid_through_m
            month_label = f'{month} *' if is_paid_through else month
            row1_cells = []
            row2_cells = []
            for j, year in enumerate(years):
                cells = self.format_payment_cells_for(year, month_number)
                payments_this_month = cells[2]
                if payments_this_month:
                    year_totals[j] = year_totals[j] + payments_this_month
                cell1 = cells[0]
                cell2 = cells[1]
                payments_date = f'{year}-{month_number}'
                out_of_range = payments_date < self.member_from or payments_date > self.member_through
                cls1 = ' non-member' if out_of_range else ''
                cls2 = cls1
                cls1 = f'{cls1} {cell1.cls}'
                cls2 = f'{cls2} {cell2.cls}'
                row1_cells.append(f'<td class="cell{cls1}">{esc(cell1.text)}</td>')
                row2_cells.append(f'<td class="cell{cls2}">{esc(cell2.text)}</td>')
            row1_cls = 'paid-through' if is_paid_through else ''
            parts.append(f'<tr class="cell1-row {row1_cls}"><th class="month">{esc(month_label)}</th>')
            parts.append(''.join(row1_cells))
            parts.append('</tr>')
            parts.append('<tr class="cell2-row"><th class="month"></th>')
            parts.append(''.join(row2_cells))
            parts.append('</tr>')
        parts.append('</tbody><tfoot><tr><th></th>')
        for t in year_totals:
            val = f'${round(t, 2)}' if t else ''
            parts.append(f'<td class="total">{esc(val)}</td>')
        parts.append('</tr></tfoot></table>')
        return ''.join(parts)

    def format_payment_cells_for(self, year, month_number) -> tuple[Cell, Cell, float]:
        cell1 = Cell('', '')
        cell2 = Cell('', '')
        payments_this_month = None
        payments_date = f'{year}-{month_number}'
        all_payments = self.payments + self.historical_payments()
        info = self.payment_info(all_payments, payments_date)
        if info is not None:
            if info == (None, None, None, None, None):
                cell1 = ARCHIVE_CELL
                cell2 = ARCHIVE_CELL
            else:
                method = info[0]
                identifier = info[1] or ''
                amount = info[2]
                payments_this_month = info[3]
                previous = self.payment_info(all_payments, date_of_previous_month(year, int(month_number)))
                following = self.payment_info(all_payments, date_of_next_month(year, int(month_number)))
                if info == previous:
                    cell1 = JAN_CONTINUITY_CELL if month_number == '01' else CONTINUITY_CELL
                    cell2 = DOWN_ARROW_CELL
                    if info == following:
                        cell2 = DEC_CONTINUITY_CELL if month_number == '12' else CONTINUITY_CELL
                else:
                    cell1 = Cell(f' {method} {identifier}'.rstrip(), 'begin-of-range')
                    cell2 = Cell(f'${amount}' if amount else '?', 'range-amount' if info == following else 'end-of-range')
        return (cell1, cell2, payments_this_month)

    def format_legend(self):
        left = []
        right = []

        left.append(NON_MEMBER_CELL.text)
        right.append('not a member or former member')

        left.append(ARCHIVE_CELL.text)
        right.append('archived, see paper cards')

        for method in self.payment_methods.values():
            left.append(method.display_short or method.method)
            right.append(method.display_long)

        return (
                '\n────────────────────────────────────────────────────────────\n'
                f'{format_two_columns(left, right, TABLE_CELL_WIDTH+2)}'
                )

    def format_html_legend(self):
        left = []
        right = []
        left.append(('', 'non-member'))
        right.append(('not a member or former member', ''))
        left.append((ARCHIVE_CELL.text, 'archive'))
        right.append(('archived, see paper cards', ''))
        for method in self.payment_methods.values():
            left.append((method.display_short or method.method, ''))
            right.append((method.display_long, ''))
        parts = ['<table class="card-legend">']
        for l, r in zip(left, right):
            left_text, left_cls = l
            right_text, right_cls = r
            parts.append(
                f'<tr><td class="legend-symbol {left_cls}">{html_module.escape(str(left_text))}</td>'
                f'<td class="legend-desc {right_cls}">{html_module.escape(str(right_text))}</td></tr>'
            )
        parts.append('</table>')
        return f'<div class="card-legend-container">{"".join(parts)}</div>'

    def payment_info(self, payments, date):
        payments_with_date = [payment for payment in payments if payment.paid_from <= date <= payment.paid_through]
        if len(payments_with_date) > 0:
            found = payments_with_date[0]
            method = self.convert_payment_method(found.method)
            identifier = found.identifier
            amount = found.amount
            date = found.date
            number_of_payments = number_of_payments_between(found.paid_from, found.paid_through)
            payments_this_month = None
            if number_of_payments is not None and amount is not None:
                amount = decimal.Decimal(amount)
                payments_this_month = amount/number_of_payments
            return (method, identifier, amount, payments_this_month, date)
        return None

    def convert_payment_method(self, method):
        if not method:
            return None
        methodrow = self.payment_methods[method] or {}
        return methodrow.display_short or method

def date_of_previous_month(year, month_number):
    y = year
    m = month_number - 1
    if month_number == 1:
        y = year - 1
        m = 12
    return f'{y}-{m:02}'

def date_of_next_month(year, month_number):
    y = year
    m = month_number + 1
    if month_number == 12:
        y = year + 1
        m = 1
    return f'{y}-{m:02}'

def format_date(date):
    split = date.split('-') if date else []
    if len(split) >= 2:
        year = split[0]
        month = MONTHS_DICT[split[1]]
        return f'{month} {year}'
    else:
        return None

def format_line(values, top_sep = '┬', bottom_sep = '┼'):
    line0 = f'{top_sep}{top_sep}{top_sep}{top_sep}{top_sep}{top_sep}'
    line1 =  '      '
    line2 = f'{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}'
    for value in values:
        line0 = f'{line0}{"" :{top_sep}<{TABLE_CELL_WIDTH}}{top_sep}'
        line1 = f'{line1}{value:^{TABLE_CELL_WIDTH}} '
        line2 = f'{line2}{"" :{bottom_sep}<{TABLE_CELL_WIDTH}}{bottom_sep}'
    return f'{line0}\n{line1}\n{line2}'

def format_header(values):
    return format_line(values, '━', '─')

def format_footer(values):
    return format_line(values, '─', '━')

def date_to_months(date):
    split = date.split('-')
    try:
        if len(split) >= 2:
            return int(split[0]) * 12 + int(split[1])
        else:
            return None
    except:
        return None

def number_of_payments_between(date_from, date_thru):
    # from pudb import set_trace; set_trace()
    months_from = date_to_months(date_from)
    months_thru = date_to_months(date_thru)
    if months_from is None or months_thru is None:
        return None
    return abs(months_thru - months_from) + 1

def pop(lst):
    if len(lst) == 0:
        return None
    return lst.pop(0)

def format_two_columns(left, right, width):
    result = None
    left = list(left)
    right = list(right)
    while True:
        s_left = pop(left)
        s_right = pop(right)
        if s_left is None and s_right is None:
            break
        s_left = s_left or ''
        s_right = s_right or ''
        line = f'{s_left : <{width}}{s_right}'
        result = f'{result}\n{line}' if result else line
    return result or ''

def _add_payment_method(dict, row):
    dict[row.method] = row
    return dict

def load_payment_methods():
    rows = db.session.scalars(db.select(PaymentMethod)).all()
    return reduce(_add_payment_method, rows, {})

def get_last_name(member_name):
    if member_name:
        return member_name.split(',')[0].strip()
    return None

def get_first_name(member_name):
    if member_name:
        parts = member_name.split(',')
        return parts[1].strip() if len(parts) > 1 else None
    return None
