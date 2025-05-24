from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import time

app = Flask(__name__)

TAB_LABELS = {
    "overview": "Overview",
    "damage_stats": "Damage Stats",
    "weapon_breakdowns": "Weapon Breakdowns",
    "player_matchups": "Player Matchups"
}

def extract_stat_rows(page):
    return page.evaluate("""
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

def scrape_cta_match(match_id):
    url = f"https://cta.armorcritical.com/game.php?matchID={match_id}"
    data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        for key, label in TAB_LABELS.items():
            try:
                page.click(f"a:has-text('{label}')")
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"❌ Failed to click tab {label}: {e}")
                data[key] = []
                continue

            # Retry for 10s max
            start = time.time()
            players = []
            while time.time() - start < 10:
                players = extract_stat_rows(page)
                if players:
                    break
                page.wait_for_timeout(1000)

            # Format result for each tab
            tab_results = []
            for player in players:
                kills, deaths, dd, dt = player["kills"], player["deaths"], player["dd"], player["dt"]
                dr = dd / dt if dt > 0 else 0
                raw_cf = dd * 2.0 + dr * 3.0 + kills * 2.0 - deaths * 2.0 + 10
                cf_100 = round((raw_cf / 11000) * 100, 2)
                tab_results.append({
                    "name": player["name"],
                    "kills": kills,
                    "deaths": deaths,
                    "dd": dd,
                    "dt": dt,
                    "dr": round(dr, 2),
                    "raw_cf": round(raw_cf, 2),
                    "cf_100": cf_100
                })

            data[key] = tab_results
            print(f"✅ Tab '{label}' scraped with {len(tab_results)} players.")

        browser.close()

    return data

@app.route('/cta/<int:match_id>')
def get_match_stats(match_id):
    try:
        all_data = scrape_cta_match(match_id)
        return jsonify(all_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
