import time
from pyrogram import Client

from src.core.config import settings
from src.cryptorank_scrapper import CryptorankScrapper
from src.core.logger import get_logger

logger = get_logger(name=__name__)

from src.storage.database_main import table_funds

class PyrogramSender:
    def __init__(self):
        self.client = self.get_client()
        self.scrapper = CryptorankScrapper()


    API_ID = settings.API_ID
    API_HASH = settings.API_HASH
    SESSION_NAME = settings.SESSION_NAME
    CHAT_ID = settings.CHAT_ID
    CHAT_ID_EN = settings.CHAT_ID_EN


    def get_client(self):
        client = Client(
            self.SESSION_NAME,
            api_id=self.API_ID,
            api_hash=self.API_HASH
        )
        return client

    async def start_sending(self):
        print("Запуск start_sending...")  # ДОБАВИТЬ
        await self.client.start()
        print("Клиент запущен!")  # ДОБАВИТЬ
        logger.info(f"Подключились к сессии телеграмма | session_name: {self.SESSION_NAME}")

        # Заполняем базу данных при старте (один раз)
        logger.info("Инициализация базы данных фандингов...")
        self.scrapper.fill_database()
        logger.info("База данных инициализирована")

        while True:
            try:
                # Получаем все новые фандинги (проверяем последние 5)
                new_funds_messages = self.scrapper.get_all_new_funds_with_messages()
                
                if new_funds_messages:
                    logger.info(f"Найдено {len(new_funds_messages)} новых фандингов")
                    
                    # Отправляем сообщение для каждого нового фандинга
                    for fund_data in new_funds_messages:
                        try:
                            message = fund_data['message']
                            message_en = fund_data.get('message_en')
                            fund_key = fund_data['key']
                            fund_stage = fund_data['stage']
                            
                            # Отправляем русское сообщение
                            if message:
                                await self.client.send_message(self.CHAT_ID, message, disable_web_page_preview=True)
                                logger.info(f"Сообщение успешно отослано | chat_id: {self.CHAT_ID} | fund: {fund_key}_{fund_stage}")
                            else:
                                logger.warning(f"Сообщение имеет тип NoneType: {message}")
                            
                            # Отправляем английское сообщение
                            if message_en:
                                await self.client.send_message(self.CHAT_ID_EN, message_en, disable_web_page_preview=True)
                                logger.info(f"English message sent | chat_id: {self.CHAT_ID_EN} | fund: {fund_key}_{fund_stage}")
                            else:
                                logger.warning(f"English message is NoneType: {message_en}")
                            
                            # Проверяем количество фандингов в базе и удаляем самый старый при превышении лимита
                            fund_count = table_funds.get_fund_count()
                            if fund_count > settings.SIZE_OF_TEMPORAL_FUNDS_STORAGE:
                                table_funds.del_oldest_fund()
                                logger.info(f"Удален самый старый фандинг. Текущее количество: {fund_count - 1}")
                        except Exception as e:
                            logger.error(f"Ошибка при отправке сообщения: {e}")
                
                time.sleep(settings.CHECK_DELAY)
            except Exception as e:
                logger.warning(f"Ошибка в start_sending: {e}")
