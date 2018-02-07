import logging
from datetime import datetime
from urllib.parse import urlunparse, urlencode, urlparse, parse_qs

import requests
from retrying import retry

from travelcheck.util import retry_if_result_none

LOGGER = logging.getLogger(__name__)


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000,
       retry_on_result=retry_if_result_none)
def subscribe(subscription):
    host = "https://api.skypicker.com/flights"

    query = {
        'flyFrom': subscription['origin'],
        'to': subscription['destination'],
        'dateFrom': subscription['earliest_date'].strftime("%d/%m/%Y"),
        'dateTo': subscription['latest_date'].strftime("%d/%m/%Y"),
        'daysInDestinationFrom': subscription['min_days'],
        'daysInDestinationTo': subscription['max_days'],
        'curr': subscription['currency'],
        'locale': subscription['locale'],
        'directFlights': 1,
        # 'partner': 'picky',
        'partner_market': 'de',
        'sort': 'price',
        'asc': 1
    }

    url = host + '?' + urlencode(query)

    response = requests.get(url)

    if response.json() and response.json()['data']:
        first_result = response.json()['data'][0]
        subscription_response = dict()
        subscription_response['price'] = first_result['price']

        subscription_response['lastChecked'] = datetime.utcnow()

        subscription_response['outboundDate'] = datetime.utcfromtimestamp(first_result['dTimeUTC'])

        first_return_leg = next(leg for leg in first_result['route'] if lambda x: x['return'] == 1)
        subscription_response['inboundDate'] = datetime.utcfromtimestamp(
            first_return_leg['dTimeUTC'])

        subscription_response['deeplink'] = get_deeplink(first_result['deep_link'],
                                                         subscription['deeplink'])

        return subscription_response

    return None


def get_deeplink(link, type):
    if type == "flight":
        url = urlparse(link)
        query = parse_qs(url)
        query.pop('flightsId')
        query.pop('booking_token')
        url._replace(query=urlencode(query, True))
        return urlunparse(url)
    else:
        return link
