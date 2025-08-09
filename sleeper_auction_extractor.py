import csv
import os
from pathlib import Path
import time
import requests

LEAGUE_ID = "780973719656284160"
OUTDIR = Path("sleeper_drafts_csv")
RATE_DELAY = 0.25  # be nice to their API

BASE = "https://api.sleeper.app/v1"

def get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    OUTDIR.mkdir(exist_ok=True)

    # Map roster_id -> owner user_id, and user_id -> display_name/team_name
    rosters = get(f"{BASE}/league/{LEAGUE_ID}/rosters")  # roster_id, owner_id, etc.
    time.sleep(RATE_DELAY)
    users = get(f"{BASE}/league/{LEAGUE_ID}/users")      # user_id, display_name, metadata.team_name
    time.sleep(RATE_DELAY)

    roster_owner = {r["roster_id"]: r.get("owner_id") for r in rosters}
    user_map = {
        u["user_id"]: {
            "username": u.get("username"),
            "display_name": u.get("display_name"),
            "team_name": (u.get("metadata") or {}).get("team_name")
        } for u in users
    }

    # Fetch all drafts for the league (includes previous seasons)
    drafts = get(f"{BASE}/league/{LEAGUE_ID}/drafts")
    time.sleep(RATE_DELAY)

    if not drafts:
        print("No drafts found for this league.")
        return

    for d in drafts:
        draft_id = d["draft_id"]
        # Draft metadata: season, type (auction/snake), status, etc.
        dmeta = get(f"{BASE}/draft/{draft_id}")
        time.sleep(RATE_DELAY)

        # Picks (auction + snake share same endpoint)
        picks = get(f"{BASE}/draft/{draft_id}/picks")
        time.sleep(RATE_DELAY)

        season = dmeta.get("season")
        dtype = dmeta.get("type")     # "auction" or "snake"
        status = dmeta.get("status")
        teams = dmeta.get("settings", {}).get("teams")
        draft_name = dmeta.get("metadata", {}).get("name")

        # Prepare CSV
        fname = OUTDIR / f"sleeper_draft_{season}_{draft_id}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "season","draft_id","draft_name","draft_type","status","num_teams",
                "round","pick_no","overall_slot","nomination","auction_price",
                "player_id","first_name","last_name","position","team",
                "picked_by_user_id","picked_by_display","picked_by_team_name",
                "roster_id","is_keeper"
            ])

            for p in picks:
                md = p.get("metadata") or {}
                first = md.get("first_name")
                last = md.get("last_name")
                pos = md.get("position")
                nfl_team = md.get("team")
                player_id = md.get("player_id")

                # Auction price (if auction). Sleeper puts the winning bid in metadata.amount
                auction_price = md.get("amount")  # may be None for snake drafts

                # Some drafts also show the nominated player's name in metadata (rarely needed)
                nomination = md.get("nomination") or None

                picked_by_user = p.get("picked_by")  # user_id
                roster_id = p.get("roster_id")
                owner_user = picked_by_user or roster_owner.get(roster_id)

                uinfo = user_map.get(owner_user, {})
                disp = uinfo.get("display_name") or uinfo.get("username")
                team_name = uinfo.get("team_name")

                w.writerow([
                    season, draft_id, draft_name, dtype, status, teams,
                    p.get("round"), p.get("pick_no"), p.get("draft_slot"),
                    nomination, auction_price,
                    player_id, first, last, pos, nfl_team,
                    owner_user, disp, team_name,
                    roster_id, p.get("is_keeper"),
                ])

        print(f"Wrote {fname}")

if __name__ == "__main__":
    main()
