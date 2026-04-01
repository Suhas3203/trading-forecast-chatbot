import requests
from bs4 import BeautifulSoup
from datetime import datetime


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_ipo_gmp() -> dict:
    """Scrape live IPO GMP data from investorgain.com"""
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        table = soup.find("table", {"id": "mainTable"})
        if not table:
            table = soup.find("table", class_=lambda c: c and "table" in c)
        if not table:
            return {"error": "Could not parse IPO GMP table", "data": []}

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]
        ipos = []

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 5:
                continue

            # Typical columns: IPO Name, Price, GMP, Est Listing, Last Updated
            try:
                ipo = {
                    "name": cols[0],
                    "price": cols[1],
                    "gmp": cols[2],
                    "estimated_listing": cols[3],
                    "last_updated": cols[4] if len(cols) > 4 else "",
                }
                # Skip rows that look like headers
                if any(kw in ipo["name"].lower() for kw in ["ipo name", "company"]):
                    continue
                ipos.append(ipo)
            except (IndexError, ValueError):
                continue

        return {
            "source": "investorgain.com",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            "count": len(ipos),
            "data": ipos[:20],  # top 20
        }

    except requests.exceptions.Timeout:
        return {"error": "Request timed out fetching IPO GMP data", "data": []}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}", "data": []}
    except Exception as e:
        return {"error": f"Failed to parse IPO GMP: {str(e)}", "data": []}


def get_upcoming_ipos() -> dict:
    """Scrape upcoming IPO listings from investorgain.com"""
    url = "https://www.investorgain.com/report/upcoming-ipo/333/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        table = soup.find("table", {"id": "mainTable"})
        if not table:
            table = soup.find("table", class_=lambda c: c and "table" in c)
        if not table:
            return {"error": "Could not parse upcoming IPO table", "data": []}

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]
        ipos = []

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 4:
                continue
            try:
                ipo = {
                    "name": cols[0],
                    "open_date": cols[1],
                    "close_date": cols[2],
                    "price_band": cols[3],
                    "lot_size": cols[4] if len(cols) > 4 else "",
                    "issue_size": cols[5] if len(cols) > 5 else "",
                }
                if any(kw in ipo["name"].lower() for kw in ["ipo name", "company"]):
                    continue
                ipos.append(ipo)
            except (IndexError, ValueError):
                continue

        return {
            "source": "investorgain.com",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            "count": len(ipos),
            "data": ipos[:15],
        }

    except Exception as e:
        return {"error": f"Failed to fetch upcoming IPOs: {str(e)}", "data": []}
