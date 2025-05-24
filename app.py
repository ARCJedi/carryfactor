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

        # Wait for all scripts and AJAX to complete
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Click all tab buttons to potentially trigger DOM rendering
        for tab in ["Overview", "Damage Stats", "Weapon Breakdowns", "Player Matchups"]:
            try:
                page.click(f"a:has-text('{tab}')")
                page.wait_for_timeout(400)
            except Exception as e:
                print(f"Could not click tab '{tab}':", e)

        # Extract all stat rows directly via JS DOM
        players = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll("tr"));
                return rows.map(row => {
                    const cols = row.querySelectorAll("td");
                    if (cols.length >= 5 && row.innerHTML.includes("box-score-name")) {
                        return {
                            name: cols[0].textContent.trim(),
                            kills: parseInt(cols[1].textContent.trim()),
                            deaths: parseInt(cols[2].textContent.trim()),
                            dd: parseInt(cols[3].textContent.trim()),
                            dt: parseInt(cols[4].textContent.trim())
                        };
                    }
                    return null;
                }).filter(Boolean);
            }
        """)

        browser.close()

    if not players:
        print("No stat rows found.")
        return []

    results = []
    for player in players:
        kills = player["kills"]
        deaths = player["deaths"]
        dd = player["dd"]
        dt = player["dt"]
        dr = dd / dt if dt > 0 else 0
        raw_cf = dd * 2.0 + dr * 3.0 + kills * 2.0 - deaths * 2.0 + 10
        cf_100 = round((raw_cf / 11000) * 100, 2)
        results.append({
            "name": player["name"],
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
