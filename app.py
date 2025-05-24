from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

def scrape_cta_match(match_id):
    url = f"https://cta.armorcritical.com/game.php?matchID={match_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        # Click all the tabs to reveal hidden content
        for tab in ["Overview", "Damage Stats", "Weapon Breakdowns", "Player Matchups"]:
            try:
                page.click(f"a:has-text('{tab}')")
                page.wait_for_timeout(300)
            except Exception as e:
                print(f"Could not click tab '{tab}':", e)

        # Wait for everything to finish rendering
        page.wait_for_timeout(1000)

        # Get full inner HTML (this ensures we see toggled tab content)
        html = page.inner_html("body")
        browser.close()

        # Log some of the captured HTML for debugging
        print("=== HTML BODY START ===")
        print(html[:5000])
        print("=== HTML BODY END ===")

        # Extract player stats using regex
        pattern = re.compile(
            r"<td class=['\"]box-score-name['\"]>(.*?)</td>\s*"
            r"<td>(\d+)</td>\s*"
            r"<td>(\d+)</td>\s*"
            r"<td>(\d+)</td>\s*"
            r"<td>(\d+)</td>"
        )

        results = []
        for match in pattern.finditer(html):
            name, kills, deaths, dd, dt = match.groups()
            kills, deaths, dd, dt = map(int, [kills, deaths, dd, dt])
            dr = dd / dt if dt > 0 else 0
            raw_cf = dd * 2.0 + dr * 3.0 + kills * 2.0 - deaths * 2.0 + 10
            cf_100 = round((raw_cf / 11000) * 100, 2)
            results.append({
                "name": name,
                "kills": kills,
                "deaths": deaths,
                "dd": dd,
                "dt": dt,
                "dr": round(dr, 2),
                "raw_cf": round(raw_cf, 2),
                "cf_100": cf_100
            })

        return results

@app.route('/cta/<int:match_id>')
def get_match_stats(match_id):
    try:
        data = scrape_cta_match(match_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
