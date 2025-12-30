"""GFA Lüneburg API Client for fetching waste collection data."""
import logging
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

SERVLET_URL = "https://portal.gfa-lueneburg.de:8443/WasteManagementLueneburg/WasteManagementServlet"


class HiddenInputParser(HTMLParser):
    """Parser for extracting hidden input fields from HTML."""

    def __init__(self):
        super().__init__()
        self._args = {}
        self._cities = []
        self._streets = []
        self._house_numbers = []
        self._current_select = None

    @property
    def args(self) -> dict[str, str]:
        """Return parsed hidden input fields."""
        return self._args

    @property
    def cities(self) -> list[str]:
        """Return list of available cities."""
        return self._cities

    @property
    def streets(self) -> list[str]:
        """Return list of available streets."""
        return self._streets

    @property
    def house_numbers(self) -> list[str]:
        """Return list of available house numbers."""
        return self._house_numbers

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle HTML start tags."""
        if tag == "input":
            d = dict(attrs)
            if str(d.get("type", "")).lower() == "hidden":
                name = d.get("name")
                if name:
                    self._args[name] = d.get("value", "")
        elif tag == "select":
            d = dict(attrs)
            name = d.get("name", "")
            if name == "Ort":
                self._current_select = "cities"
            elif name == "Strasse":
                self._current_select = "streets"
            elif name == "Hausnummer":
                self._current_select = "house_numbers"
        elif tag == "option" and self._current_select:
            d = dict(attrs)
            value = d.get("value", "")
            if value:
                # Replace &nbsp; with regular space
                value = value.replace("\xa0", " ").replace("&nbsp;", " ")
                if self._current_select == "cities":
                    self._cities.append(value)
                elif self._current_select == "streets":
                    self._streets.append(value)
                elif self._current_select == "house_numbers":
                    self._house_numbers.append(value)

    def handle_endtag(self, tag: str) -> None:
        """Handle HTML end tags."""
        if tag == "select":
            self._current_select = None


class GFALueneburgAPI:
    """API client for GFA Lüneburg waste calendar."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self._session: aiohttp.ClientSession | None = None
        self._args: dict[str, str] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_cities(self) -> list[str]:
        """Fetch the list of available cities."""
        session = await self._get_session()

        async with session.get(
            SERVLET_URL,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "FALSE"},
            timeout=30,
        ) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        self._args = parser.args
        
        return parser.cities

    async def get_streets(self, city: str) -> list[str]:
        """Fetch the list of streets for a given city."""
        session = await self._get_session()

        # First, get the initial page to get session data
        if not self._args:
            await self.get_cities()

        args = self._args.copy()
        args["Zeitraum"] = f"Jahresübersicht {datetime.now().year}"
        args["Ort"] = city
        args["Strasse"] = ""
        args["Hausnummer"] = ""
        args["Method"] = "POST"
        args["SubmitAction"] = "CITYCHANGED"
        args["Focus"] = "Ort"

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        self._args = parser.args
        
        return parser.streets

    async def get_house_numbers(self, city: str, street: str) -> list[str]:
        """Fetch the list of house numbers for a given city and street."""
        session = await self._get_session()

        # Ensure we have streets loaded
        if not self._args:
            await self.get_streets(city)

        args = self._args.copy()
        args["Zeitraum"] = f"Jahresübersicht {datetime.now().year}"
        args["Ort"] = city
        args["Strasse"] = street
        args["Hausnummer"] = ""
        args["Method"] = "POST"
        args["SubmitAction"] = "STREETCHANGED"
        args["Focus"] = "Strasse"

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        self._args = parser.args
        
        return parser.house_numbers

    async def get_ics_calendar(
        self, city: str, street: str, house_number: str
    ) -> str:
        """Fetch the ICS calendar data for a given address."""
        session = await self._get_session()

        # Step 1: Initial page
        async with session.get(
            SERVLET_URL,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "FALSE"},
            timeout=30,
        ) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        args = parser.args

        # Step 2: Select city
        args["Zeitraum"] = f"Jahresübersicht {datetime.now().year}"
        args["Ort"] = city
        args["Strasse"] = street
        args["Hausnummer"] = str(house_number)
        args["Method"] = "POST"
        args["SubmitAction"] = "CITYCHANGED"
        args["Focus"] = "Ort"

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        args = parser.args

        # Step 3: Select street
        args["Zeitraum"] = f"Jahresübersicht {datetime.now().year}"
        args["Ort"] = city
        args["Strasse"] = street
        args["Hausnummer"] = str(house_number)
        args["Method"] = "POST"
        args["SubmitAction"] = "STREETCHANGED"
        args["Focus"] = "Strasse"

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        args = parser.args

        # Step 4: Forward to results
        args["Zeitraum"] = f"Jahresübersicht {datetime.now().year}"
        args["Ort"] = city
        args["Strasse"] = street
        args["Hausnummer"] = str(house_number)
        args["SubmitAction"] = "forward"

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            text = await response.text()

        parser = HiddenInputParser()
        parser.feed(text)
        args = parser.args

        # Step 5: Download ICS
        args["ApplicationName"] = "com.athos.kd.lueneburg.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        args["IsLastPage"] = "true"
        args["Method"] = "POST"
        args["PageName"] = "Terminliste"
        
        # Remove address fields for ICS download
        for key in ["Zeitraum", "Ort", "Strasse", "Hausnummer"]:
            args.pop(key, None)

        async with session.post(SERVLET_URL, data=args, timeout=30) as response:
            response.raise_for_status()
            ics_content = await response.text()

        return ics_content
