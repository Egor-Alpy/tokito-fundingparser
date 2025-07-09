# libraries
import logging
import os
import datetime

# data
from src.core.config import settings

# config: parameters
LOG_FORMAT = '%(asctime).19s | %(levelname).3s | %(message)s'
LOG_DATE_TIME = '%Y-%m-%d %H:%M:%S'

# config: filename
LOG_DIRECTORY = 'data/logs/'
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)
LOG_FILENAME = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f.log')
LOG_FILEPATH = os.path.join(LOG_DIRECTORY, LOG_FILENAME)

# config: setting
logging.basicConfig(
    level=logging.WARNING,  # Изменено с INFO на WARNING для файлового логирования
    format=LOG_FORMAT,
    datefmt=LOG_DATE_TIME,
    filename=LOG_FILEPATH,
)

# console: stream handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# console: formatter
console_formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(console_formatter)

# dt_logger: session
logger = logging.getLogger(settings.PROJECT_NAME)
logger.addHandler(console_handler)