import datetime
import logging
import os

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

CHESSNUT_CLUB_ID = os.environ.get("CHESSNUT_CLUB_ID")
CACHE_TIMEOUT = 60 * 60 * 24


def response_excerpt(response, limit=1000):
    body = response.text.replace("\n", " ").replace("\r", " ").strip()
    return body[:limit]


def log_unexpected_response(response, endpoint):
    logger.error(
        "Chessnut API returned an unexpected response: endpoint=%s status=%s "
        "content_type=%s requested_url=%s final_url=%s body=%r",
        endpoint,
        response.status_code,
        response.headers.get("Content-Type"),
        response.request.url if response.request else "unknown",
        response.url,
        response_excerpt(response),
    )


def datetime_parser(dct):
    for k, v in dct.items():
        if "date" in k and isinstance(v, str):
            dct[k] = datetime.date.fromisoformat(v)
    return dct


class Chessnut:
    _cache_key = "chessnut_events"
    _api_key = None

    def __init__(self):
        super().__init__()

    @classmethod
    def api_key(cls):
        if not cls._api_key:
            api_key = os.environ.get("CHESSNUT_API_KEY", "").strip()
            if len(api_key) >= 2 and api_key[0] == api_key[-1] and api_key[0] in "\"'":
                api_key = api_key[1:-1].strip()
            if not api_key:
                raise ValueError("CHESSNUT_API_KEY environment variable not set")
            cls._api_key = api_key
        return cls._api_key

    @staticmethod
    def get_all_chessnut_events(*, start_date=None, end_date=None) -> list[dict]:
        if cache.get(Chessnut._cache_key) is not None:
            return cache.get(Chessnut._cache_key)
        print("Fetching chessnut events...")

        headers = {"Authorization": f"Bearer {Chessnut.api_key()}"}
        params = {
            "start_date": None if start_date is None else start_date.isoformat(),
            "end_date": None if end_date is None else end_date.isoformat(),
        }
        endpoint = (
            f"https://chessnut.club/api/v1/club/{CHESSNUT_CLUB_ID}/events/fetch-all"
        )
        try:
            response = requests.get(
                endpoint,
                headers={**headers, "Accept": "application/json"},
                params=params,
                timeout=15,
            )
        except requests.RequestException:
            logger.exception("Chessnut API request failed: endpoint=%s", endpoint)
            return []
        if response.status_code != 200:
            log_unexpected_response(response, "fetch-all")
            return []

        try:
            result = response.json(object_hook=datetime_parser)["events"]
        except (ValueError, KeyError, TypeError):
            log_unexpected_response(response, "fetch-all")
            return []
        cache.set(Chessnut._cache_key, result, CACHE_TIMEOUT)
        print("Fetched chessnut events")
        return result or []

    @staticmethod
    def get_chessnut_event_by_id(chessnut_event_id: int):
        print(f"Fetching chessnut event: {chessnut_event_id}")
        headers = {"Authorization": f"Bearer {Chessnut.api_key()}"}
        params = {}
        endpoint = f"https://chessnut.club/api/v1/events/{chessnut_event_id}"
        try:
            response = requests.get(
                endpoint,
                headers={**headers, "Accept": "application/json"},
                params=params,
                timeout=15,
            )
        except requests.RequestException:
            logger.exception("Chessnut API request failed: endpoint=%s", endpoint)
            return None
        if response.status_code != 200:
            log_unexpected_response(response, "event-detail")
            return None
        try:
            result = response.json(object_hook=datetime_parser)["event"]
        except (ValueError, KeyError, TypeError):
            log_unexpected_response(response, "event-detail")
            return None
        return result
