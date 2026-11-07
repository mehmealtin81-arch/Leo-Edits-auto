
import json
import urllib.request
from datetime import datetime, timezone, timedelta

URLS = [
    "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_matches():
    all_events = []

    for url in URLS:
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                all_events.extend(data.get("events", []))
        except Exception as error:
            print("Kaynak okunamadı:", url, error)

    return all_events

def is_galatasaray(team):
    name = team.get("team", {}).get("displayName", "").lower()
    return "galatasaray" in name

def main():
    events = get_matches()
    now = datetime.now(timezone.utc)

    matches = []

    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue

        competitors = competitions[0].get("competitors", [])
        gs = next((x for x in competitors if is_galatasaray(x)), None)

        if not gs:
            continue

        opponent = next((x for x in competitors if x is not gs), {})
        date_text = event.get("date")

        if not date_text:
            continue

        date = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
        status = event.get("status", {}).get("type", {})

        matches.append({
            "date": date,
            "opponent": opponent.get("team", {}).get("displayName", "Bilinmiyor"),
            "completed": status.get("completed", False),
            "score": gs.get("score", "?"),
            "opponent_score": opponent.get("score", "?"),
            "competition": event.get("season", {}).get("name", event.get("name", "Organizasyon")),
            "event": event
        })

    print("GALATASARAY MAÇ TAKİP RAPORU")
    print("=" * 35)

    upcoming = [m for m in matches if m["date"] >= now and not m["completed"]]
    previous = [m for m in matches if m["completed"]]

    if upcoming:
        match = min(upcoming, key=lambda x: x["date"])
        local_date = match["date"].astimezone(
            timezone(timedelta(hours=3))
        )
        print("\nYAKLAŞAN MAÇ")
        print("Rakip:", match["opponent"])
        print("Tarih:", local_date.strftime("%d.%m.%Y %H:%M"))
        print("Organizasyon:", match["competition"])
    else:
        print("\nYaklaşan maç bulunamadı veya kaynakta yer almıyor.")

    if previous:
        match = max(previous, key=lambda x: x["date"])
        print("\nSON OYNANAN MAÇ")
        print("Galatasaray", match["score"], "-", match["opponent_score"], match["opponent"])
        print("Tarih:", match["date"].strftime("%d.%m.%Y"))

        summary_url = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer/"
            "tur.1/summary?event=" + match["event"]["id"]
        )

        try:
            request = urllib.request.Request(summary_url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                summary = json.loads(response.read().decode("utf-8"))

            scorers = []
            for play in summary.get("plays", []):
                if play.get("scoringPlay"):
                    scorer = play.get("participants", [])
                    for person in scorer:
                        athlete = person.get("athlete", {})
                        if athlete.get("displayName"):
                            scorers.append(athlete["displayName"])

            print("Gol bilgileri:", ", ".join(scorers) if scorers else "Doğrulanmış golcü bilgisi bulunamadı.")
        except Exception as error:
            print("Golcü bilgisi alınamadı:", error)
    else:
        print("\nSon maç bulunamadı.")

    if not events:
        raise RuntimeError("Hiçbir veri kaynağından maç bilgisi alınamadı.")

if __name__ == "__main__":
    main()
