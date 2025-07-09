import sqlite3 as sq

from src.storage.tables.table_funds import TableFunds


FILENAME_DATABASE = "database.db"

connection = sq.connect(database=FILENAME_DATABASE)
cursor = connection.cursor()

table_funds = TableFunds(connection, cursor)

for table in [table_funds]:
    table.execute_table()