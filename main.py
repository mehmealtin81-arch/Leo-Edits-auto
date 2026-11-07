import json
import urllib.request
from datetime import datetime, timezone

URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/teams/galatasaray/schedule"

def get_matches():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    data = get_matches()
    events = data.get("events", [])

    now = datetime.now(timezone.utc)

    matches = []
    for event in events:
        competition = event.get("name", "Galatasaray maçı")
        date_text = event.get("date")

        if not date_text:
            continue

        date = datetime.fromisoformat(date_text.replace("Z", "+00:00"))

        competitions = event.get("competitions", [])
        if not competitions:
            continue

        competitors = competitions[0].get("competitors", [])
        gs = next(
            (team for team in competitors
             if team.get("team", {}).get("id") == "994"),
            None
        )

        if not gs:
            continue

        opponent = next(
            (team for team in competitors if team is not gs),
            {}
        )

        status = event.get("status", {}).get("type", {})
        completed = status.get("completed", False)

        matches.append({
            "date": date,
            "name": competition,
            "opponent": opponent.get("team", {}).get("displayName", "Bilinmiyor"),
            "completed": completed,
            "score": gs.get("score"),
            "opponent_score": opponent.get("score"),
            "event": event
        })

    upcoming = [m for m in matches if m["date"] >= now and not m["completed"]]
    previous = [m for m in matches if m["completed"]]

    print("GALATASARAY MAÇ TAKİP RAPORU")
    print("=" * 35)

    if upcoming:
        match = min(upcoming, key=lambda m: m["date"])
        print("\nYAKLAŞAN MAÇ")
        print("Rakip:", match["opponent"])
        print("Tarih:", match["date"].astimezone().strftime("%d.%m.%Y %H:%M"))
        print("Organizasyon:", match["name"])
    else:
        print("\nYaklaşan maç bilgisi bulunamadı.")

    if previous:
        match = max(previous, key=lambda m: m["date"])
        print("\nSON OYNANAN MAÇ")
        print("Galatasaray", match["score"], "-", match["opponent_score"], match["opponent"])
        print("Tarih:", match["date"].astimezone().strftime("%d.%m.%Y"))

        try:
            details = match["event"].get("competitions", [{}])[0]
            scorers = []
            for competitor in details.get("competitors", []):
                for item in competitor.get("leaders", []):
                    if item.get("name") == "goals":
                        for athlete in item.get("leaders", []):
                            scorers.append(
                                athlete.get("athlete", {}).get("displayName", "Bilinmiyor")
                            )
            if scorers:
                print("Gol bilgileri:", ", ".join(scorers))
        except Exception:
            pass

if __name__ == "__main__":
    main()
