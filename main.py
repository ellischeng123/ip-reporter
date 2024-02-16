from zoneinfo import ZoneInfo
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import json
import sys

import requests

IP_FILE = '.ip.json'
SLACK_TOKEN_FILE = '.slack.json'

PUB_IP_CHECK_API = 'https://api.ipify.org?format=json'
SLACK_POST_MSG_API = 'https://slack.com/api/chat.postMessage'

LOG_FORMAT = '{asctime} [{levelname:7}] {name}s {message}'


def setup_logger() -> None:
    handlers = [
        RotatingFileHandler(filename='ip-reporter.log', encoding='utf-8', maxBytes=64 * 1024, backupCount=1),
        logging.StreamHandler(sys.stdout)
    ]
    logging.basicConfig(
        format=LOG_FORMAT, style='{', handlers=handlers, level=logging.INFO
    )


def load_previous_ip_from_file() -> str:
    with open(IP_FILE) as ipf:
        j = json.load(ipf)
        prev_ip = j['ip']
        return prev_ip


def get_current_ip() -> str:
    r = requests.get(PUB_IP_CHECK_API)
    r.raise_for_status()

    return r.json()['ip']


def format_ip_msg(prev_ip: str, cur_ip: str) -> list[dict]:
    msg = []

    status = '❌ IP HAS CHANGED' if prev_ip != cur_ip else '✅ IP NOT CHANGED'
    now = datetime.now(tz=ZoneInfo('Asia/Taipei')).isoformat(timespec="seconds")
    msg.append({
        'type': 'header',
        'text': {
            'type': 'plain_text',
            'text': f'{status}{" " * 2}@{" " * 2}{now}'
        }
    })

    msg.append({
        'type': 'section',
        'fields': [
            {
                'type': 'mrkdwn',
                'text': f'▶ {cur_ip}'
            },
            {
                'type': 'mrkdwn',
                'text': f'⏮ {prev_ip}'
            }
        ]
    })

    return msg


def send_msg_to_slack(msg: str, channel: str = 'dev') -> None:
    token = 'NO-TOKEN'
    with open(SLACK_TOKEN_FILE) as f:
        j = json.load(f)
        token = j['token']

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {token}'
    }

    body = {
        'channel': channel,
        'blocks': msg
    }

    r = requests.post(SLACK_POST_MSG_API, json=body, headers=headers)

    r.raise_for_status()

    resp = r.json()

    if not resp or not resp['ok']:
        raise ValueError(f'Slack responded with: {resp["error"]}')


if __name__ == '__main__':
    setup_logger()

    logger = logging.getLogger()
    logger.info('Starting ip-reporter')

    try:
        prev_ip = load_previous_ip_from_file()
        logger.info(f'Previous ip was: {prev_ip}')

        cur_ip = get_current_ip()
        logger.info(f'Current ip is: {cur_ip}')

        msg = format_ip_msg(prev_ip, cur_ip)
        send_msg_to_slack(msg)
        logger.info('Message sent')

    except Exception as e:
        logger.exception('error')
