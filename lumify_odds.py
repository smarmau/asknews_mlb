"""
Lumify odds provider for the MLB betting bot.

Fetches multi-book moneylines from https://lumify.ai and returns the same
shape used by ScrapeSportsbookreview / OddsCache:

  {
    "date": "...",
    "home_team": "...",
    "away_team": "...",
    "id": "...",
    "home_ml": {"draftkings": -140, "fanduel": -138, ...},
    "away_ml": {"draftkings": 120, ...},
  }

Free instant key (no signup): https://lumify.ai/docs/ai
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pytz
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("LUMIFY_BASE_URL", "https://lumify.ai").rstrip("/")
BOOKMAKER = os.environ.get("LUMIFY_BOOKMAKER", "all")


def _normalize(name: str) -> str:
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


class LumifyOddsProvider:
    """Drop-in odds source when LUMIFY_API_KEY is set."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("LUMIFY_API_KEY") or "").strip()
        if not self.api_key:
            raise ValueError("LUMIFY_API_KEY is required for LumifyOddsProvider")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "asknews-mlb/lumify",
            }
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        resp = self._session.get(
            f"{BASE_URL}{path}", params=params or {}, timeout=60
        )
        resp.raise_for_status()
        return resp.json()

    def _list_event_ids(self) -> List[int]:
        ids: List[int] = []
        for status in ("scheduled", "inprogress"):
            after_id = None
            while True:
                params: Dict[str, Any] = {
                    "sport": "mlb",
                    "status": status,
                    "limit": 50,
                }
                if after_id is not None:
                    params["after_id"] = after_id
                payload = self._get("/v1/events", params)
                for ev in payload.get("events") or []:
                    if ev.get("id") is not None:
                        ids.append(int(ev["id"]))
                after_id = payload.get("next_after_id")
                if not payload.get("events") or after_id is None:
                    break
        return ids

    @staticmethod
    def _participants(event: dict) -> Tuple[str, str]:
        home = away = ""
        for p in event.get("participants") or []:
            role = (p.get("role") or "").lower()
            name = (
                (p.get("team") or {}).get("name")
                or p.get("name")
                or ""
            )
            if role == "home":
                home = name
            elif role == "away":
                away = name
        return home, away

    @staticmethod
    def _moneyline_maps(
        odds_payload: dict, home: str, away: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        home_ml: Dict[str, Any] = {}
        away_ml: Dict[str, Any] = {}
        home_n, away_n = _normalize(home), _normalize(away)
        for book in odds_payload.get("bookmakers") or []:
            bookmaker = book.get("bookmaker") or "unknown"
            for market in book.get("markets") or []:
                if (market.get("key") or "").lower() not in ("h2h", "moneyline"):
                    if (market.get("label") or "").lower() != "moneyline":
                        continue
                for outcome in market.get("outcomes") or []:
                    name = outcome.get("outcome") or ""
                    price = outcome.get("price")
                    n = _normalize(name)
                    if not n or price is None:
                        continue
                    # Prefer exact / substring match against home/away team names
                    if home_n and (n == home_n or home_n in n or n in home_n):
                        home_ml[bookmaker] = price
                    elif away_n and (n == away_n or away_n in n or n in away_n):
                        away_ml[bookmaker] = price
        return home_ml, away_ml

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_games(self) -> List[dict]:
        """Return today's MLB games with multi-book moneylines."""
        games: List[dict] = []
        for event_id in self._list_event_ids():
            try:
                event = self._get(
                    f"/v1/events/{event_id}",
                    {"include_odds": "true", "bookmaker": BOOKMAKER},
                )
            except requests.HTTPError as exc:
                logger.warning("Lumify event %s failed: %s", event_id, exc)
                continue

            home, away = self._participants(event)
            if not home or not away:
                continue
            odds_payload = event.get("odds") or {}
            home_ml, away_ml = self._moneyline_maps(odds_payload, home, away)
            starts = event.get("starts_at") or datetime.now(
                pytz.timezone("America/New_York")
            ).isoformat()
            games.append(
                {
                    "date": starts,
                    "home_team": home,
                    "away_team": away,
                    "id": f"{starts}_{away}_{home}",
                    "lumify_event_id": event_id,
                    "home_ml": home_ml,
                    "away_ml": away_ml,
                }
            )
        logger.info("Lumify returned %d MLB games with odds", len(games))
        return games

    def find_game(self, away_team: str, home_team: str) -> Optional[dict]:
        away_n, home_n = _normalize(away_team), _normalize(home_team)
        for game in self.fetch_games():
            if (
                _normalize(game["away_team"]) == away_n
                or away_n in _normalize(game["away_team"])
                or _normalize(game["away_team"]) in away_n
            ) and (
                _normalize(game["home_team"]) == home_n
                or home_n in _normalize(game["home_team"])
                or _normalize(game["home_team"]) in home_n
            ):
                return game
        return None
