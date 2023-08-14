import os
import telegram
import requests
import time
import logging

from dotenv import load_dotenv

from exceptions import ResponseNot200

logging.basicConfig(
    level=logging.INFO,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s')

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция проверяет доступность переменных окружения.
    Которые необходимы для работы программы.
    """
    if PRACTICUM_TOKEN is None:
        logging.critical('bug')
        raise SystemExit
    elif TELEGRAM_TOKEN is None:
        logging.critical('bug')
        raise SystemExit
    elif TELEGRAM_CHAT_ID is None:
        logging.critical('bug')
        raise SystemExit


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('ok')
    except Exception:
        logging.error('bug')


def get_api_answer(timestamp):
    """Функция делает запрос к  эндпоинту API-сервиса."""
    try:
        if ENDPOINT is None:
            logging.error('error - ENDPOINTE = None')
            return print('error - ENDPOINTE = None')
        url = ENDPOINT
    except Exception as error:
        print(error)
        logging.error(error)
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(url, headers=HEADERS, params=payload)
        if homework_statuses.status_code != 200:
            raise ResponseNot200('Not 200')
        response = homework_statuses.json()
    except requests.exceptions.RequestException as error:
        print(error)
    else:
        return response


def check_response(response):
    """Функция проверяет ответ API на соответствие документации."""
    try:
        homeworks = response['homeworks']
        return homeworks[round(len(homeworks) - 1)]
    except KeyError('homeworks') as error:
        print(error)
        logging.error(error)
    except TypeError('homeworks') as error:
        print(error)
    except IndexError('homeworks') as error:
        print(error)
    except Exception as error:
        print(error)
        logging.error(error)


def parse_status(homework):
    """Функция извлекает из информации.
    О конкретной домашней работе статус этой работы.
    """
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except TypeError('status') as error:
        message = error
        logging.error(error)
        return message
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())
    except Exception:
        raise SystemExit
    if bot is None:
        raise SystemExit
    elif timestamp is None:
        raise SystemExit
    while True:
        try:
            check_tokens()
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
