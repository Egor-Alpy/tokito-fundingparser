from src.storage.database import DataBase

from src.core.logger import get_logger

from src.core.enums import KeyFunds

logger = get_logger(name=__name__)


class TableFunds(DataBase):
    table_name = "funds"

    def execute_table(self):
        if self.database:
            logger.info(f"Database: table '{self.table_name}' has been connected!")

        self.database.execute(f"""CREATE TABLE IF NOT EXISTS funds (
            {KeyFunds.fund_id} INTEGER PRIMARY KEY AUTOINCREMENT,
            {KeyFunds.fund_key} TEXT,
            {KeyFunds.fund_stage} TEXT,
            {KeyFunds.concat_key_stage} TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        self.database.commit()

    def get_all_concat_key_stage(self):
        self.cursor.execute(f"SELECT {KeyFunds.concat_key_stage} FROM funds")
        rows_tuples = self.cursor.fetchall()
        rows = []
        for i in range(len(rows_tuples)):
            rows.append(rows_tuples[i][0])
        return rows

    def add_fund(self, key: str, stage: str) -> None:
        try:
            self.cursor.execute(
                f"INSERT OR IGNORE INTO funds({KeyFunds.fund_key}, {KeyFunds.fund_stage}, {KeyFunds.concat_key_stage}) "
                f"VALUES('{key}', '{stage}', '{key}_{stage}')")
            if self.cursor.rowcount == 0:
                logger.debug(f"Фандинг уже существует: {key}_{stage}")
            self.database.commit()
        except Exception as e:
            logger.error(f"Error adding fund: {e}")

    def del_fund(self, concat_key_stage: str):
        self.cursor.execute(f"DELETE FROM funds WHERE {KeyFunds.concat_key_stage} = '{concat_key_stage}'")
        self.database.commit()
    
    def del_oldest_fund(self):
        """Удаляет самый старый фандинг из базы"""
        self.cursor.execute(f"DELETE FROM funds WHERE {KeyFunds.fund_id} = (SELECT MIN({KeyFunds.fund_id}) FROM funds)")
        self.database.commit()
    
    def get_fund_count(self):
        """Возвращает количество фандингов в базе"""
        self.cursor.execute("SELECT COUNT(*) FROM funds")
        return self.cursor.fetchone()[0]
