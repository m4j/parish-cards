from sys import argv
import StJohnDC
import re
from datetime import datetime
import os
import sys

def formatMemberName(row):
    ruName = row['RU Member Patronymic']
    ruName = '' if ruName is None else (' ' + ruName)
    return '%s, %s%s (%s, %s)' % (row['RU Member Last'], row['RU Member First'], ruName, row['Member Last'], row['Member First'])

def printErrorIncorrect():
    print('--------------------')
    print('Incorrect, try again')
    print('--------------------')

def pickByIndex(rows):
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
            printErrorIncorrect()
            continue
        if selected-1 not in range(0, count):
            printErrorIncorrect()
            continue
        return selected-1

def findMember(member, picker=pickByIndex):
    selected = '%' + member + '%'
    cursor = conn.cursor()
    cursor.execute(StJohnDC.sql_cards_by_name, {'name': selected})
    rows = cursor.fetchall()
    formatted = list(map(formatMemberName, rows))
    index = picker(formatted)
    return None if index is None else rows[index]

def findMemberDues(member):
    cursor = conn.cursor()
    queryParameters = {
        'fname': member['Member First'],
        'lname': member['Member Last'],
    }
    cursor.execute(StJohnDC.sql_dues_by_member, queryParameters)
    return cursor.fetchall()

def paymentMethodShort(method):
    if method == 'Check':
        return '✓'
    if method == 'Discover':
        return 'DISC'
    if method == 'PayPal':
        return 'PP'
    return method

def dateToMonths(date):
    split = date.split('-')
    try:
        if len(split) >= 2:
            return int(split[0]) * 12 + int(split[1])
        else:
            return None
    except:
        return None

def numberOfDuesBetween(dateFrom, dateThru):
    # from pudb import set_trace; set_trace()
    monthsFrom = dateToMonths(dateFrom)
    monthsThru = dateToMonths(dateThru)
    if monthsFrom is None or monthsThru is None:
        return None
    return abs(monthsThru - monthsFrom) + 1

def paymentInfo(rows, date):
    foundRows = [row for row in rows if row['Paid From'] <= date <= row['Paid Through']]
    if len(foundRows) > 0:
        found = foundRows[0]

        method = paymentMethodShort(found['Method']) or '?'
        identifier = found['Identifier'] or ''

        monthlyDue = None
        numberOfDues = numberOfDuesBetween(found['Paid From'], found['Paid Through'])
        amount = found['Amount']
        if numberOfDues is not None and amount is not None:
            monthlyDue = int(found['Amount'])/numberOfDues

        return (method, identifier, monthlyDue)
    return None

def historicalMemberDues(dateFrom, dateThru):
    return [{
            'Amount' : None,
            'Identifier' : None,
            'Method' : None,
            'Paid From' : dateFrom,
            'Paid Through' : dateThru,
            }]

def formatLine(values, topSep = '┬', bottomSep = '┼'):
    line0 = f'─────{topSep}'
    line1 =  '     │'
    line2 = f'─────{bottomSep}'
    for value in values:
        line0 = f'{line0}{"" :─<{StJohnDC.table_cell_width}}{topSep}'
        line1 = f'{line1}{value:^{StJohnDC.table_cell_width}}│'
        line2 = f'{line2}{"" :─<{StJohnDC.table_cell_width}}{bottomSep}'
    print(line0)
    print(line1)
    print(line2)

def formatHeader(values):
    formatLine(values, '┬', '┼')

def formatFooter(values):
    formatLine(values, '┼', '┴')

def formatMemberDuesTable(member):
    print(formatMemberName(member))
    dues = findMemberDues(member)
    firstFrom = dues[0]['Paid From'] if len(dues) > 0 else '2019-01'
    firstFrom = min(firstFrom, '2019-01')
    lastThrough = dues[-1]['Paid Through'] if len(dues) > 0 else '2024-12'
    lastThrough = max(lastThrough, '2024-12')
    firstYear = int(firstFrom.split('-')[0])
    lastYear = int(lastThrough.split('-')[0])
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    monthNumbers = ['01','02','03','04','05','06','07','08','09','10','11','12']
    formatHeader(range(firstYear, lastYear + 1))
    yearTotals = list(map(lambda y: 0, range(firstYear, lastYear + 1)))
    for i, month in enumerate(months):
        row1 = f' {month} │'
        row2 = '     │'
        monthNumber = monthNumbers[i]
        for j, year in enumerate(range(firstYear, lastYear + 1)):
            cell1 = ''
            cell2 = ''
            duesDate = f'{year}-{monthNumber}'
            memberFrom = member['Member From'] or StJohnDC.distant_past
            if duesDate < memberFrom:
                cell1 = f'{"" :░<{StJohnDC.table_cell_width}}'
                cell2 = cell1
            else:
                historicalPaidThru = member['Dues Paid Through'] or StJohnDC.distant_past
                allDues = historicalMemberDues(memberFrom, historicalPaidThru) + dues
                info = paymentInfo(allDues, duesDate)
                if info is not None:
                    method = info[0]
                    identifier = info[1]
                    cell1 = f' {method} {identifier}'.rstrip()
                    thisMonthDues = info[2] 
                    cell2 = '?'
                    if thisMonthDues:
                        cell2 = f'${thisMonthDues}'
                        yearTotals[j] = yearTotals[j] + thisMonthDues
            row1 = f'{row1}{cell1:<{StJohnDC.table_cell_width}}│'
            row2 = f'{row2}{cell2:^{StJohnDC.table_cell_width}}│'
        print(row1)
        print(row2)
    formattedYearTotals = list(map(lambda t: f'${t}' if t else '', yearTotals))
    formatFooter(formattedYearTotals)

try:
    script, arg_member = argv
except ValueError:
    print('Missing argument')
    exit(-1)
database = os.environ['STJB_DATABASE']
conn = StJohnDC.connect(database)
memberRow = findMember(arg_member)
if memberRow:
    formatMemberDuesTable(memberRow)
else:
    print('Нет данных (not found)', file=sys.stderr)

