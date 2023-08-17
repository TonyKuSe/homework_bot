import logging
import os
import requests
import time

import telegram
from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import (
    CodeNot200Error, GetApiNot200Error, KeyNoneError,
    NotTokenIdError
)

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
    check_list = (
        (PRACTICUM_TOKEN, 'подключения телеграм'),
        (TELEGRAM_TOKEN, 'подключения телеграм'),
        (TELEGRAM_CHAT_ID, 'подключения к чату'),
    )
    for token, error_str in check_list:
        if token is None:
            logging.critical(f'Недоступны данные для {error_str}')
            raise NotTokenIdError


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        logging.debug('Сообщение отправленно')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправленно')
    except telegram.error.TelegramError as error:
        logging.error(f'Сбой отправки сообщения. {error}')


def get_api_answer(timestamp):
    """Функция делает запрос к  эндпоинту API-сервиса."""
    try:
        url = ENDPOINT
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        logging.error(error)
        return message
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(url, headers=HEADERS, params=payload)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise GetApiNot200Error(
                f'Ошибка статус ответа {homework_statuses.status_code}')
        response = homework_statuses.json()
    except requests.exceptions.RequestException as error:
        raise CodeNot200Error(error)
    else:
        return response


def check_response(response):
    """Функция проверяет ответ API на соответствие документации."""
    logging.debug('Start check')
    if not isinstance(response, dict):
        raise TypeError
    if 'homeworks' not in response:
        raise KeyNoneError('KeyNone homeworks')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError
    return homeworks[round(len(homeworks) - len(homeworks))]


def parse_status(homework):
    """Функция извлекает информации.
    О конкретной домашней работе статус этой работы.
    """
    if 'homework_name' not in homework:
        raise KeyNoneError('KeyNone homework_name')
    homework_name = homework.get('homework_name')
    if 'status' not in homework:
        raise KeyNoneError('KeyNone status')
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyNoneError('KeyNone status in HOMEWORK_VERDICTS')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    message_retro = ''
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(0)
    except Exception as error:
        message = f'Сбой в работе программы: {error}'
        raise SystemExit
    if bot is None:
        message = 'Сбой в работе программы: Нет данных бота'
        logging.critical('Нет данных бота')
        raise SystemExit
    elif timestamp is None:
        message = 'Сбой в работе программы: Нет данных времени'
        raise SystemExit
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date', int(time.time()))
            homework = check_response(response)
            message = parse_status(homework)
            if message == message_retro:
                continue
            send_message(bot, message)
            message_retro = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s')
    main()
