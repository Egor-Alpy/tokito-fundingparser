import time
import asyncio

from src.pyrogram_sender import PyrogramSender
from src.core.logger import get_logger

logger = get_logger(name=__name__)



def main():
    while True:
        try:
            asyncio.run(PyrogramSender().start_sending())
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()


