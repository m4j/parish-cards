from sys import argv
import StJohnDC
import re
from datetime import datetime
import os
import sys

class Member:

    def __init__(self, row):
        self.row = row

    def formatName(self, member):
        ruName = self.row[f'RU {member} Patronymic']
        ruName = '' if ruName is None else (' ' + ruName)
        name = '%s, %s%s (%s, %s)' % (self.row[f'RU {member} Last'], self.row[f'RU {member} First'], ruName, self.row[f'{member} Last'], self.row[f'{member} First'])
        return f'{name} †' if self.row[f'{member} Status'] == 'Deceased' else name

    def formatMemberName(self):
        return self.formatName('Member')

    def formatSpouseName(self):
        return self.formatName('Spouse')

    def __getitem__(self, key):
        return self.row[key]

def formatMemberDetails(row):
    status = row['Member Status']
    spouseStatus = ''
    name = row.formatMemberName()
    spouse = ''
    if row['Spouse First'] and row['Spouse Last']:
        spouse = row.formatSpouseName()
        spouseStatus = row['Spouse Status']
        spouseType = row['Spouse Type']
        spouseStatus = f'{spouseType}, {spouseStatus}'
    duesAmount = row['Dues Amount']
    memberFrom = formatDate(row['Member From']) or '?'
    address = row['Address']
    city = row['City']
    state = row['State/Region']
    postalCode = row['Postal Code']
    plus4 = row['Plus 4']
    zipCode = postalCode + (f'-{plus4}' if plus4 else '')
    cityStateZip = f'{city}, {state} {zipCode}'
    email = row['E-Mail Address']
    phones = []
    homePhone = row['Home Phone']
    if homePhone:
        phones.append(f'{homePhone} (home)')
    mobilePhone = row['Mobile Phone']
    if mobilePhone:
        phones.append(f'{mobilePhone} (mobile)')
    workPhone = row['Work Phone']
    if workPhone: 
        phones.append(f'{workPhone} (work)')
    phonesLine = ', '.join(phones)
    memberFrom = formatDate(row['Member from']) or '?'

    result = (
        f'✼ {name : <55}{status}\n'
        f'  {spouse : <55}{spouseStatus}\n'
        f'{address : <57}Monthly dues: ${duesAmount}\n'
        f'{cityStateZip : <57}Member from {memberFrom}\n'
        f'{phonesLine}'
    )
    if email:
        result = f'{result}\n{email}'
    return result

def findMember(member, picker=StJohnDC.pickByIndex):
    selected = '%' + member + '%'
    cursor = conn.cursor()
    cursor.execute(StJohnDC.sql_cards_by_name, {'name': selected})
    rows = cursor.fetchall()
    members = list(map(Member, rows))
    formatted = list(map(Member.formatMemberName, members))
    index = picker(formatted)
    return None if index is None else members[index]

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

def formatDate(date):
    split = date.split('-') if date else []
    if len(split) >= 2:
        year = split[0]
        month = StJohnDC.months_dict[split[1]]
        return f'{month} {year}'
    else:
        return None

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
        identifier = found['Identifier']
        amount = found['Amount']
        date = found['Date']
        numberOfDues = numberOfDuesBetween(found['Paid From'], found['Paid Through'])
        duesThisMonth = None
        if numberOfDues is not None and amount is not None:
            duesThisMonth = int(amount)/numberOfDues
        return (method, identifier, amount, duesThisMonth, date)
    return None

def historicalMemberDues(dateFrom, dateThru):
    return [{
            'Date' : None,
            'Amount' : None,
            'Identifier' : None,
            'Method' : None,
            'Paid From' : dateFrom,
            'Paid Through' : dateThru,
            }]

def formatLine(values, topSep = '┬', bottomSep = '┼'):
    line0 = f'{topSep}{topSep}{topSep}{topSep}{topSep}{topSep}'
    line1 =  '      '
    line2 = f'{bottomSep}{bottomSep}{bottomSep}{bottomSep}{bottomSep}{bottomSep}'
    for value in values:
        line0 = f'{line0}{"" :{topSep}<{StJohnDC.table_cell_width}}{topSep}'
        line1 = f'{line1}{value:^{StJohnDC.table_cell_width}} '
        line2 = f'{line2}{"" :{bottomSep}<{StJohnDC.table_cell_width}}{bottomSep}'
    print(line0)
    print(line1)
    print(line2)

def formatHeader(values):
    formatLine(values, '━', '─')

def formatFooter(values):
    formatLine(values, '─', '━')

def dateOfPreviousMonth(year, monthNumber):
    y = year
    m = monthNumber - 1
    if monthNumber == 1:
        y = year - 1
        m = 12
    return f'{y}-{m:02}'

def dateOfNextMonth(year, monthNumber):
    y = year
    m = monthNumber + 1
    if monthNumber == 12:
        y = year + 1
        m = 1
    return f'{y}-{m:02}'

def formatPaymentCellsFor(member, year, monthNumber):
    cell1 = ''
    cell2 = ''
    duesThisMonth = None
    duesDate = f'{year}-{monthNumber}'
    memberFrom = member['Member From'] or StJohnDC.distant_past
    if duesDate < memberFrom:
        cell1 = f'{"" :░<{StJohnDC.table_cell_width}}'
        cell2 = cell1
    else:
        historicalPaidThru = member['Dues Paid Through'] or StJohnDC.distant_past
        allDues = findMemberDues(member) + historicalMemberDues(memberFrom, historicalPaidThru)
        info = paymentInfo(allDues, duesDate)
        if info is not None:
            if info == (None, None, None, None, None):
                cell1 = '...'
                cell2 = '...'
            else:
                method = info[0]
                identifier = info[1] or ''
                amount = info[2] 
                duesThisMonth = info[3]
                previous = paymentInfo(allDues, dateOfPreviousMonth(year, int(monthNumber)))
                if info == previous:
                    cell1 = '─╮ ' if monthNumber == '01' else '│'
                    following = paymentInfo(allDues, dateOfNextMonth(year, int(monthNumber)))
                    cell2 = '▼'
                    if info == following:
                        cell2 = '     ╰─▶︎   ' if monthNumber == '12' else '│'
                else:
                    cell1 = f' {method} {identifier}'.rstrip()
                    cell2 = f'${amount}' if amount else '?'
    return (cell1, cell2, duesThisMonth)

def formatMemberDuesTable(member):
    print(formatMemberDetails(member))
    dues = findMemberDues(member)
    firstFrom = dues[0]['Paid From'] if len(dues) > 0 else '2019-01'
    firstFrom = min(firstFrom, '2019-01')
    lastThrough = dues[-1]['Paid Through'] if len(dues) > 0 else '2024-12'
    lastThrough = max(lastThrough, '2024-12')
    firstYear = int(firstFrom.split('-')[0])
    lastYear = int(lastThrough.split('-')[0])
    formatHeader(range(firstYear, lastYear + 1))
    yearTotals = list(map(lambda y: 0, range(firstYear, lastYear + 1)))
    for i, month in enumerate(StJohnDC.months):
        row1 = f' {month}  '
        row2 = '      '
        monthNumber = StJohnDC.month_numbers[i]
        for j, year in enumerate(range(firstYear, lastYear + 1)):
            cells = formatPaymentCellsFor(member, year, monthNumber)
            duesThisMonth = cells[2]
            if duesThisMonth:
                yearTotals[j] = yearTotals[j] + duesThisMonth
            cell1 = cells[0]
            cell2 = cells[1]
            row1 = f'{row1}{cell1:^{StJohnDC.table_cell_width}} '
            row2 = f'{row2}{cell2:^{StJohnDC.table_cell_width}} '
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
member = findMember(arg_member)
if member:
    #print(list(memberRow))
    formatMemberDuesTable(member)
else:
    print('Нет данных (not found)', file=sys.stderr)

