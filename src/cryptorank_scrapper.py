from datetime import datetime
from bs4 import BeautifulSoup
import httpx
import json

from src.storage.database_main import table_funds
from src.core.logger import logger


class CryptorankScrapper:
    def __init__(self):
        pass

    url = 'https://api.cryptorank.io/v0/funding-rounds-v2'
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://cryptorank.io',
        'priority': 'u=1, i',
        'referer': 'https://cryptorank.io/',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "YaBrowser";v="25.4", "Yowser";v="2.5"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 YaBrowser/25.4.0.0 Safari/537.36'
    }
    def get_body(self, limit=10, skip=0):
        """Возвращает тело запроса с указанным лимитом и смещением"""
        return {
            "limit": min(limit, 20),  # API возвращает максимум 20 записей
            "filters": {},
            "skip": skip,
            "sortingColumn": "date",
            "sortingDirection": "DESC"
        }

    def fill_database(self):
        """Заполняем базу данных начальными фандингами + проверяем новые"""
        try:
            # Получаем все существующие фандинги из БД
            existing_funds = set(table_funds.get_all_concat_key_stage())
            logger.info(f"В базе данных уже есть {len(existing_funds)} фандингов")
            
            # Запрашиваем последние 5 фандингов из API
            logger.debug(f"Запрашиваем последние 5 фандингов из API...")
            funds = self.get_funds(limit=5)

            if not funds:
                logger.warning(f"Не удалось получить фандинги из API!")
                return None

            logger.debug(f"Получено {len(funds)} фандингов из API")

            # Добавляем только те фандинги, которых еще нет в БД
            new_funds_count = 0
            for fund in funds:
                key = fund.get('key')
                stage = fund.get('stage')
                if key and stage:
                    fund_id = f"{key}_{stage}"
                    if fund_id not in existing_funds:
                        try:
                            table_funds.add_fund(key=key, stage=stage)
                            new_funds_count += 1
                            logger.info(f"Добавлен новый фандинг в базу: {fund_id}")
                        except Exception as e:
                            logger.error(f"Ошибка при добавлении фандинга в базу: {e}")
                    else:
                        logger.debug(f"Фандинг {fund_id} уже существует в БД, пропускаем")

            logger.info(f"Добавлено {new_funds_count} новых фандингов в базу")
            return None
        except Exception as e:
            logger.error(f"Ошибка при заполнении базы данных: {e}")
            return None

    @staticmethod
    def get_social_links_and_category(fund_key):
        """Получаем ссылки на соц сети проекта со страницы проекта"""
        html = httpx.get(f'https://cryptorank.io/price/{fund_key}').text
        soup = BeautifulSoup(html, 'html.parser')
        result = {}

        # Находим все ссылки
        for link in soup.find_all('a', class_='styles_coin_social_link_item__SAH_3'):
            href = link.get('href')
            span = link.find('span')

            if href and span and span.text:
                result[span.text] = href
        category = soup.find('p', class_='sc-b2e3d974-0 sc-ff306fb2-3 cqdNHy')
        return result, category

    @staticmethod
    def get_twitterscore_url(twitter_url):
        """Создаем ссылку на твиттер скор"""
        if not twitter_url:
            return None

        url = twitter_url.rstrip('/')
        username = url.split('/')[-1]

        if username and not username.startswith('@'):
            return f"https://twitterscore.io/twitter/{username}/overview/"

        return None

    @staticmethod
    def get_all_new_funds(current_funds: list[dict]):
        """Получает все новые фандинги из списка"""
        # Получаем актуальный список всех фандингов из БД
        existing_funds = set(table_funds.get_all_concat_key_stage())
        new_funds = []

        # Проверяем все полученные фандинги в обратном порядке (от старых к новым)
        current_funds = current_funds[::-1]

        for current_fund in current_funds:
            try:
                current_fund_key = current_fund.get('key')
                current_fund_stage = current_fund.get('stage')
                if current_fund_key and current_fund_stage:
                    current_fund_concat_key_stage = current_fund_key + "_" + current_fund_stage
                    # Проверяем, есть ли уже такой фандинг в БД
                    if current_fund_concat_key_stage not in existing_funds:
                        # Добавляем в БД только если его там еще нет
                        table_funds.add_fund(key=current_fund_key, stage=current_fund_stage)
                        new_funds.append(current_fund)
                        # Добавляем в set, чтобы избежать дубликатов в текущей сессии
                        existing_funds.add(current_fund_concat_key_stage)
                        logger.info(f"Найден новый фандинг: {current_fund_concat_key_stage}")
                    else:
                        logger.debug(f"Фандинг {current_fund_concat_key_stage} уже существует в БД")
            except Exception as e:
                logger.error(f"Error: {e}")
        return new_funds

    def get_funds(self, limit=10, skip=0):
        """Делаем запрос в апи для получения основной инфы"""
        try:
            with httpx.Client() as client:
                response = client.post(url=self.url, headers=self.headers, json=self.get_body(limit, skip))
                response.raise_for_status()

                result = response.json()
                funds = result.get('data')
                if funds:
                    return funds
                return None
        except httpx.RequestError as e:
            return f"Ошибка запроса: {e}"
        except httpx.HTTPStatusError as e:
            return f"HTTP ошибка: {e.response.status_code} - {e.response.text}"
        except json.JSONDecodeError as e:
            return f"Ошибка декодирования JSON: {e}"


    def get_all_new_funds_with_messages(self):
        """Получает все новые фандинги и генерирует для них сообщения"""
        try:
            with httpx.Client() as client:
                # Запрашиваем только 5 последних фандингов для проверки
                response = client.post(url=self.url, headers=self.headers, json=self.get_body(5))
                response.raise_for_status()

                result = response.json()
                funds = result.get('data')
                new_funds = self.get_all_new_funds(funds)
                
                messages = []
                for fund in new_funds:
                    message = self._generate_message_for_fund(fund)
                    if message:
                        messages.append({
                            'message': message,
                            'key': fund.get('key'),
                            'stage': fund.get('stage')
                        })
                
                return messages
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка: {e.response.status_code} - {e.response.text}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}")
            return []

    def _generate_message_for_fund(self, data):
        """Генерирует сообщение для одного фандинга"""
        try:
            if data is None:
                return None

            if type(data) is not str and type(data) is not list:
                param_names = data.keys()
            else:
                return None

            # Извлекаем все данные из словаря
            key = data.get('key')
            name = data.get('name')
            investments = data.get('raise')
            total_investments = data.get('totalRaise')
            stage = data.get('stage')
            twitter_score = data.get('twitterScore', '')
            funds_list = data.get('funds', [])
            date = data.get('date', '')
            
            # Проверяем обязательные поля
            if not name or not key:
                return None
            
            # Получаем дополнительные данные
            links = {}
            category = None
            if key:
                links, category = self.get_social_links_and_category(key)
            
            # Формируем сообщение
            message = f"**[{name}]({f'https://cryptorank.io/ru/ico/{key}'}):** \n\n"
            
            # Инвестиция
            if investments:
                message += f"**Инвестиция:** {float(investments) / 1000000} млн$\n"
            
            # Инвестиций за все время
            if total_investments:
                message += f"**Инвестиций за все время:** {float(total_investments) / 1000000} млн$\n"
            
            # Этап
            if stage:
                message += f"**Этап:** {stage}\n"
            
            # Ссылки
            if links:
                public_links = ', '.join([f'[{source_name}]({source_url})' for source_name, source_url in links.items()])
                if public_links:
                    message += f"**Ссылки:** {public_links}\n"
            
            # Твиттер скор
            if twitter_score and links.get('X'):
                twitter_score_with_link = f"[{twitter_score}]({self.get_twitterscore_url(links.get('X', ''))})"
                message += f"**Твиттер скор:** {twitter_score_with_link}\n"
            
            # Кто инвестировал
            if funds_list:
                investors_list = []
                for fund in funds_list:
                    fund_name = fund.get('name', '')
                    fund_key = fund.get('key', '')
                    if fund_name and fund_key:
                        fund_link = f"https://cryptorank.io/ru/funds/{fund_key}"
                        investors_list.append(f"[{fund_name}]({fund_link})")
                
                if investors_list:
                    investors_str = ", ".join(investors_list)
                    message += f"**Кто инвестировал:** {investors_str}\n"
            
            # Дата
            if date:
                try:
                    formatted_date = datetime.fromisoformat(date.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                    message += f"\n**Дата:** {formatted_date}\n"
                except:
                    pass
            
            # Хэштег категории
            if category:
                hashtag = '_'.join(str(category).split())
                if hashtag:
                    message += f"#{hashtag}\n"
            
            message += f"\n**[Crypto Free](https://t.me/+s1tbwyMnGrdkZTZi)** | **[Гемопарсер](https://t.me/+86qlqOCRO3xmY2Zi)** | **[Худший чат](https://t.me/+VTQXJ4vOVjJlN2Q6)** | **[Прокси](https://proxys.io/?refid=80884)**"
            
            return message

        except Exception as e:
            logger.error(f"Ошибка в части генерации сообщения для одного фандинга: {e}")
            return None