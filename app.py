
from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

def scrape_cta_match(match_id):
    url = f"https://cta.armorcritical.com/game.php?matchID={match_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(2000)  # wait for rendering
        html = page.content()
        browser.close()

        # Match each player row
        pattern = re.compile(r"<td class='box-score-name'>(.*?)</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>")
        results = []

        for match in pattern.finditer(html):
            name, kills, deaths, dd, dt = match.groups()
            kills, deaths, dd, dt = map(int, [kills, deaths, dd, dt])
            dr = dd / dt if dt != 0 else 0
            raw_cf = dd * 1.5 + dr * 2 + kills * 2 - deaths + 5
            cf_100 = round((raw_cf / 9062.5) * 100, 2)
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
    app.run(debug=True)
