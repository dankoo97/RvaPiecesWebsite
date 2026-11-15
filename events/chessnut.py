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


class ChessnutAPIError(Exception):
    """Raised when the Chessnut API can't be reached or returns an unusable response."""


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
    def get_all_chessnut_events(
        *, start_date=None, end_date=None, fail_silently=True, refresh=False
    ) -> list[dict]:
        """
        Fetch every event for the club.

        :param fail_silently: When True (the default), API failures return an empty list.
            When False, they raise ChessnutAPIError so callers can tell "the API is down"
            apart from "the club has no events".
        :param refresh: Skip the cached list and fetch from the API (the result is still cached).
        """

        def fail(message):
            if fail_silently:
                return []
            raise ChessnutAPIError(message)

        cached = None if refresh else cache.get(Chessnut._cache_key)
        if cached:
            return cached
        logger.info("Fetching chessnut events...")

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
            return fail("Chessnut API request failed")
        if response.status_code != 200:
            log_unexpected_response(response, "fetch-all")
            return fail(f"Chessnut API returned status {response.status_code}")

        try:
            result = response.json(object_hook=datetime_parser)["events"]
        except (ValueError, KeyError, TypeError):
            log_unexpected_response(response, "fetch-all")
            return fail("Chessnut API returned an unexpected response")
        if not result:
            # The club always has events, so an empty list means something went wrong upstream.
            # Don't cache it, or every page would see "no events" for a whole day.
            logger.warning("Chessnut API returned no events: endpoint=%s", endpoint)
            return fail("Chessnut API returned no events")

        cache.set(Chessnut._cache_key, result, CACHE_TIMEOUT)
        logger.info("Fetched chessnut events")
        return result

    @staticmethod
    def get_chessnut_event_by_id(chessnut_event_id: int):
        logger.info("Fetching chessnut event: %s", chessnut_event_id)
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
