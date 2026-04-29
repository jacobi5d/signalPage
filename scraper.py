import os
import json
import csv
import requests
from bs4 import BeautifulSoup

def fetch_pro_report():
    url = "https://www.actionnetwork.com/sharp-report"
    
    # Grab the session token from GitHub Secrets
    session_token = os.environ.get("AN_SESSION_TOKEN")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Cookie": f"AN_SESSION_TOKEN_V1={session_token}"
    }

    print("Fetching data from Action Network...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    return parse_html(response.text)

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    games_data = []

    # Find the main data table
    table = soup.find('table', role='table')
    if not table:
        print("Could not find the data table. Session token might be expired or page structure changed.")
        return []

    tbody = table.find('tbody')
    rows = tbody.find_all('tr', recursive=False)

    for row in rows:
        cells = row.find_all('td', recursive=False)
        
        # Skip promo/free game rows that don't have the full 10 columns
        if len(cells) < 10:
            continue

        try:
            # 1. Matchup Info
            teams = [t.text.strip() for t in cells[0].find_all('span') if t.text.strip()]
            matchup = " @ ".join(teams) if len(teams) >= 2 else "Unknown Matchup"
            
            # 2. Open Odds & 3. Best Odds
            # Grabbing the text from the odds containers
            open_odds = [span.text.strip() for span in cells[1].find_all('span', class_=lambda c: c and 'css' in c)]
            best_odds = [span.text.strip() for span in cells[2].find_all('span', class_=lambda c: c and 'css' in c)]

            # 4-8. Signals (Count the SVGs/Buttons in each cell)
            sharp_action = len(cells[3].find_all('svg'))
            big_money = len(cells[4].find_all('svg'))
            pro_systems = len(cells[5].find_all('svg'))
            model_proj = len(cells[6].find_all('svg'))
            top_experts = len(cells[7].find_all('svg'))

            # 9. % Bets & 10. % Money
            bet_pcts = [div.text.strip() for div in cells[8].find_all('div') if '%' in div.text]
            money_pcts = [div.text.strip() for div in cells[9].find_all('div') if '%' in div.text]

            game = {
                "matchup": matchup,
                "open_odds": open_odds,
                "best_odds": best_odds,
                "signals": {
                    "sharp_action": sharp_action,
                    "big_money": big_money,
                    "pro_systems": pro_systems,
                    "model_proj": model_proj,
                    "top_experts": top_experts
                },
                "bet_pct": bet_pcts,
                "money_pct": money_pcts
            }
            games_data.append(game)
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return games_data

def save_data(data):
    # Save to JSON
    with open('pro_report.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("Saved to pro_report.json")

    # Save to CSV
    if data:
        keys = ["matchup", "open_odds", "best_odds", "sharp_action", "big_money", "pro_systems", "model_proj", "top_experts", "bet_pct", "money_pct"]
        with open('pro_report.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in data:
                csv_row = {
                    "matchup": row["matchup"],
                    "open_odds": " / ".join(row["open_odds"]),
                    "best_odds": " / ".join(row["best_odds"]),
                    "sharp_action": row["signals"]["sharp_action"],
                    "big_money": row["signals"]["big_money"],
                    "pro_systems": row["signals"]["pro_systems"],
                    "model_proj": row["signals"]["model_proj"],
                    "top_experts": row["signals"]["top_experts"],
                    "bet_pct": " / ".join(row["bet_pct"]),
                    "money_pct": " / ".join(row["money_pct"])
                }
                writer.writerow(csv_row)
        print("Saved to pro_report.csv")

if __name__ == "__main__":
    scraped_data = fetch_pro_report()
    if scraped_data:
        save_data(scraped_data)
    else:
        print("No data collected.")
