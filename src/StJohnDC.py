import sqlite3

def connect(database = '../../StJohnDC.db'):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

sql_cards_by_name = """select * from Cards C
            where C.[Member Last] like :name OR
                  C.[Member First] like :name OR
                  C.[Member First Other] like :name OR
                  C.[Member Middle] like :name OR
                  C.[Member Maiden] like :name OR
                  C.[RU Member Last] like :name OR
                  C.[RU Member Maiden] like :name OR
                  C.[RU Member First] like :name OR
                  C.[RU Member Patronymic] like :name
             order by [Member Last], [Member First]"""

sql_dues_by_member = """select * from Payments_Dues
            where [Member Last] like :lname AND
                  [Member First] like :fname
             order by [Paid From], [Paid Through]"""

distant_past = '1970-01'
table_cell_width = 11
