from zoneinfo import ZoneInfo
from datetime import datetime
import json
import sys

import requests

import simple_logger

IP_FILE = '.ip.json'
SLACK_TOKEN_FILE = '.slack.json'

PUB_IP_CHECK_API = 'https://api.ipify.org/?format=json'
SLACK_POST_MSG_API = 'https://slack.com/api/chat.postMessage'

logger = simple_logger.get_logger('main')


def update_ip() -> None:
    ip = get_current_ip()

    with open(IP_FILE, mode='wt') as f:
        json.dump({'ip': ip}, f)
        logger.info('IP: %s saved into %s', ip, IP_FILE)


def load_previous_ip_from_file() -> str:
    with open(IP_FILE) as ipf:
        j = json.load(ipf)
        return j['ip']


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


def send_msg_to_slack(msg, channel: str = 'dev') -> None:
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
    try:
        # update ip mode
        if len(sys.argv) > 1 and sys.argv[1] == 'update':
            logger.info('Starting ip-reporter in update mode')
            update_ip()
            sys.exit()

        # check and report
        logger.info('Starting ip-reporter in check mode')
        prev_ip = load_previous_ip_from_file()
        logger.info(f'Previous ip was: {prev_ip}')

        cur_ip = get_current_ip()
        logger.info(f'Current ip is: {cur_ip}')

        msg = format_ip_msg(prev_ip, cur_ip)
        send_msg_to_slack(msg)
        logger.info('Message sent')
        sys.exit()

    # global error handling
    except Exception as e:
        if isinstance(e, requests.HTTPError):
            logger.error('Error connecting %s', e.request.url)

            resp = e.response
            if resp is not None:
                logger.error('Status code: %s, body: %s', resp.status_code, resp.text)
        else:
            logger.exception('error')
        sys.exit(1)
