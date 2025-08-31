import time
import asyncio

from src.pyrogram_sender import PyrogramSender
from src.core.logger import logger


def main():
    # Создаем один event loop на все время работы
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            loop.run_until_complete(PyrogramSender().start_sending())
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()

