# coding=utf-8

import math
import datetime
from zoneinfo import ZoneInfo

import dateutil.parser

from framework.conf import settings


def shorten_number(value, precision=None, lang='cn'):
    levels = {
        'cn': [
            {'divisor': 1000000000000, 'unit': '万亿'},
            {'divisor': 100000000, 'unit': '亿'},
            {'divisor': 10000, 'unit': '万'},
        ],
        'en': [
            {'divisor': 1000000000, 'unit': 'B'},
            {'divisor': 1000000, 'unit': 'M'},
            {'divisor': 1000, 'unit': 'K'},
        ]
    }

    unit = ''
    for level in levels[lang]:
        if value >= level['divisor']:
            value /= level['divisor']
            unit = level['unit']
            break

    result = str(round(value, 0 if precision is None else 2))

    if precision is None:
        while result[-1] == '0':
            result = result[0:-1]

        if result[-1] == '.':
            result = result[0:-1]

    return result + unit;


def parse_date(value, tz=None):
    dt = dateutil.parser.parse(value)
    return dt.astimezone(ZoneInfo(tz or settings.TIME_ZONE))


def format_date(value, format):
    return value.strftime(format)


def semantize_date(value, format='%Y-%m-%d', lang='cn'):
    levels = [
        {
            'max': 60,
            'cn': '刚刚',
            'en': 'new',
        },
        {
            'max': 60 * 60,
            'cn': lambda x: '%s分钟前' % x,
            'en': lambda x: '%s minute%s ago' % (x, '' if x == 1 else 's'),
        },
        {
            'max': 60 * 60 * 24,
            'cn': lambda x: '%s小时前' % x,
            'en': lambda x: '%s hour%s ago' % (x, '' if x == 1 else 's'),
        },
        {
            'max': 60 * 60 * 24 * 30,
            'cn': lambda x: '%s天前' % x,
            'en': lambda x: '%s day%s ago' % (x, '' if x == 1 else 's'),
        },
        {
            'max': 60 * 60 * 24 * 30 * 12,
            'cn': lambda x: '%s个月前' % x,
            'en': lambda x: '%s month%s ago' % (x, '' if x == 1 else 's'),
        },
    ]

    delta = datetime.datetime.now() - value
    seconds = int(delta.total_seconds())

    text = ''
    for index, level in enumerate(levels):
        if seconds < level['max']:
            if index:
                text = level[lang](math.ceil(seconds/levels[index-1]['max']))
            else:
                text = level[lang]

            break

    if not text:
        text = value.strftime(format)

    return text


def parse_duration(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if hours:
        return f'{hours}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'

    return f'{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'


def compute_pager(total, page, per_page=10, count=5):
    last = math.ceil(total / per_page)
    if page > last:
        page = last

    if last <= 1:
        return dict(start=1, end=1, last=1)

    start = page
    end = page
    count = 0 if count <= 0 else count - 1

    while count:
        if count and end < last:
            end += 1
            count -= 1
            if not count:
                break

        if count and start > 1:
            start -= 1
            count -= 1
            if not count:
                break

        if start == 1 and end == last:
            break

    return dict(start=start, end=end, last=last)


FILTERS = {
    'shortennumber': shorten_number,
    'parsedate': parse_date,
    'formatdate': format_date,
    'semantizedate': semantize_date,
    'parseduration': parse_duration,
    'computepager': compute_pager,
}

TESTS = {

}
