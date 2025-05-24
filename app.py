from flask import Flask, jsonify
import os
import re
import time

# Ensure Playwright browsers are installed at runtime (Render fix)
from playwright.__main__ import main as playwright_main
from playwright.sync_api import sync_playwright

# Attempt install only if not already present
if not os.path.exists("/opt/render/.cache/ms-playwright"):
    try:
        print("🔧 Installing Playwright browsers at runtime...")
        playwright_main(["install"])
    except Exception as e:
        print("❌ Playwright browser install failed:", e)

app = Flask(__name__)

def scrape_cta_match(match_id):
    url = f"https://cta.armorcritical.com/game.php?matchID={match_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        # Click Damage Stats tab
        try:
            page.click("a:has-text('Damage Stats')")
        except Exception as e:
            print("⚠️ Could not click 'Damage Stats':", e)

        print("⏳ Waiting 10 seconds for rendering...")
        page.wait_for_timeout(10000)

        html = page.inner_html("body")
        browser.close()

        # Extract using regex fallback (brute force)
        pattern = re.compile(
            r'<td><a href="player\.php\?name=.*?">(.*?)</a></td>\s*'
            r'<td>(\d+)</td>\s*'  # kills
            r'<td>(\d+)</td>\s*'  # deaths
            r'<td>(\d+)</td>\s*'  # damage dealt
            r'<td>(\d+)</td>'     # damage taken
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
