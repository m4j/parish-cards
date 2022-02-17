from sys import argv
import StJohnDC
import re
from datetime import datetime
import os

def formatRow(row):
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
    formatted = list(map(formatRow, rows))
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
        return 'Disc'
    if method == 'PayPal':
        return 'PayP'
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

        method = paymentMethodShort(found['Method'])
        identifier = found['Identifier'] or ''
        row1 = '{} {}'.format(method, identifier)

        monthlyDue = ''
        numberOfDues = numberOfDuesBetween(found['Paid From'], found['Paid Through'])
        if numberOfDues is not None:
            monthlyDue = int(int(found['Amount'])/numberOfDues)
        row2 = '${}'.format(monthlyDue)

        return (row1, row2)
    return ('', '')

def formatMemberDuesTable(member):
    dues = findMemberDues(member)
    firstFrom = dues[0]['Paid From'] if len(dues) > 0 else '2019-01'
    firstFrom = min(firstFrom, '2019-01')
    lastThrough = dues[-1]['Paid Through'] if len(dues) > 0 else '2024-12'
    lastThrough = max(lastThrough, '2024-12')
    firstYear = int(firstFrom.split('-')[0])
    lastYear = int(lastThrough.split('-')[0])
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    monthNumbers = ['01','02','03','04','05','06','07','08','09','10','11','12']
    header1 = '    │'
    header2 = '────┼'
    header0 = '────┬'
    for year in range(firstYear, lastYear+1):
        header1 = '{} {:^10}│'.format(header1, year)
        header2 = '{}───────────┼'.format(header2)
        header0 = '{}───────────┬'.format(header0)
    print(header0)
    print(header1)
    print(header2)
    for i, month in enumerate(months):
        row1 = month + ' │'
        row2 = '    │'
        monthNumber = monthNumbers[i]
        for year in range(firstYear, lastYear+1):
            duesDate = '{}-{}'.format(year, monthNumber)
            info = paymentInfo(dues, duesDate)
            row1 = '{} {:^10}│'.format(row1,info[0])
            row2 = '{} {:^10}│'.format(row2,info[1])
        print(row1)
        print(row2)

try:
    script, arg_member = argv
except ValueError:
    print('Missing argument')
    exit(-1)
database = os.environ['STJB_DATABASE']
conn = StJohnDC.connect(database)
memberRow = findMember(arg_member)
formatMemberDuesTable(memberRow)
