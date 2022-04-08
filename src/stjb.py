import sqlite3
from abc import ABC, abstractmethod

def connect(database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

DISTANT_PAST = '1970-01'
TABLE_CELL_WIDTH = 11
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
MONTH_NUMBERS = ['01','02','03','04','05','06','07','08','09','10','11','12']
MONTHS_DICT = { number : MONTHS[int(number)-1] for number in MONTH_NUMBERS }

class AbstractMember(ABC):

    def __init__(self, row):
        self.row = row
        self.payments = []

    @abstractmethod
    def format_name(self):
        pass

    def __getitem__(self, key):
        return self.row[key]

    @property
    @abstractmethod
    def member_from(self):
        pass

    def historical_payments(self):
        return []

def print_error_incorrect():
    print('--------------------')
    print('Incorrect, try again')
    print('--------------------')

def pick_by_index(rows):
    count = len(rows)
    if count == 0:
        return None
    if count == 1:
        return 0
    while True:
        for i, row in enumerate(rows):
            print('{}) {}'.format(i+1, row))
        try:
            selected = int(input('Pick one from the list:'))
        except ValueError:
            print_error_incorrect()
            continue
        if selected-1 not in range(0, count):
            print_error_incorrect()
            continue
        return selected-1

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

def format_payment_cells_for(member, year, month_number):
    cell1 = ''
    cell2 = ''
    payments_this_month = None
    payments_date = f'{year}-{month_number}'
    member_from = member.member_from
    if payments_date < member_from:
        cell1 = f'{"" :░<{TABLE_CELL_WIDTH}}'
        cell2 = cell1
    else:
        all_payments = member.payments + member.historical_payments()
        info = payment_info(all_payments, payments_date)
        if info is not None:
            if info == (None, None, None, None, None):
                cell1 = '...'
                cell2 = '...'
            else:
                method = info[0]
                identifier = info[1] or ''
                amount = info[2] 
                payments_this_month = info[3]
                previous = payment_info(all_payments, date_of_previous_month(year, int(month_number)))
                if info == previous:
                    cell1 = '─╮ ' if month_number == '01' else '│'
                    following = payment_info(all_payments, date_of_next_month(year, int(month_number)))
                    cell2 = '▼'
                    if info == following:
                        cell2 = '     ╰─▶︎   ' if month_number == '12' else '│'
                else:
                    cell1 = f' {method} {identifier}'.rstrip()
                    cell2 = f'${amount}' if amount else '?'
    return (cell1, cell2, payments_this_month)

def print_line(values, top_sep = '┬', bottom_sep = '┼'):
    line0 = f'{top_sep}{top_sep}{top_sep}{top_sep}{top_sep}{top_sep}'
    line1 =  '      '
    line2 = f'{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}{bottom_sep}'
    for value in values:
        line0 = f'{line0}{"" :{top_sep}<{TABLE_CELL_WIDTH}}{top_sep}'
        line1 = f'{line1}{value:^{TABLE_CELL_WIDTH}} '
        line2 = f'{line2}{"" :{bottom_sep}<{TABLE_CELL_WIDTH}}{bottom_sep}'
    print(line0)
    print(line1)
    print(line2)

def print_header(values):
    print_line(values, '━', '─')

def print_footer(values):
    print_line(values, '─', '━')

def print_payments_table(member):
    payments = member.payments
    first_from = payments[0]['Paid From'] if len(payments) > 0 else '2019-01'
    first_from = min(first_from, '2019-01')
    last_through = payments[-1]['Paid Through'] if len(payments) > 0 else '2024-12'
    last_through = max(last_through, '2024-12')
    first_year = int(first_from.split('-')[0])
    last_year = int(last_through.split('-')[0])
    print_header(range(first_year, last_year + 1))
    year_totals = list(map(lambda y: 0, range(first_year, last_year + 1)))
    for i, month in enumerate(MONTHS):
        row1 = f' {month}  '
        row2 = '      '
        month_number = MONTH_NUMBERS[i]
        for j, year in enumerate(range(first_year, last_year + 1)):
            cells = format_payment_cells_for(member, year, month_number)
            payments_this_month = cells[2]
            if payments_this_month:
                year_totals[j] = year_totals[j] + payments_this_month
            cell1 = cells[0]
            cell2 = cells[1]
            row1 = f'{row1}{cell1:^{TABLE_CELL_WIDTH}} '
            row2 = f'{row2}{cell2:^{TABLE_CELL_WIDTH}} '
        print(row1)
        print(row2)
    formatted_year_totals = list(map(lambda t: f'${t}' if t else '', year_totals))
    print_footer(formatted_year_totals)

def convert_payment_method(method):
    if method == 'Check':
        return '✓'
    if method == 'Discover':
        return 'DISC'
    if method == 'PayPal':
        return 'PP'
    return method

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

def payment_info(rows, date):
    found_rows = [row for row in rows if row['Paid From'] <= date <= row['Paid Through']]
    if len(found_rows) > 0:
        found = found_rows[0]
        method = convert_payment_method(found['Method'])
        identifier = found['Identifier']
        amount = found['Amount']
        date = found['Date']
        number_of_payments = number_of_payments_between(found['Paid From'], found['Paid Through'])
        payments_this_month = None
        if number_of_payments is not None and amount is not None:
            payments_this_month = int(amount)/number_of_payments
        return (method, identifier, amount, payments_this_month, date)
    return None
