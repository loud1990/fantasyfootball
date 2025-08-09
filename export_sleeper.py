#!/usr/bin/env python3
import argparse, json, time
from typing import Dict, Any, List
import requests
import pandas as pd

API = "https://api.sleeper.app/v1"

def get(url: str) -> Any:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def main(league_id: str):
    league = get(f"{API}/league/{league_id}")
    users = get(f"{API}/league/{league_id}/users")
    rosters = get(f"{API}/league/{league_id}/rosters")
    players_all = get(f"{API}/players/nfl")  # large payload, but simplest
    # Build user lookups
    user_by_id = {u["user_id"]: u for u in users}
    display_name = {
        uid: (u.get("display_name") or u.get("username") or uid)
        for uid, u in user_by_id.items()
    }
    team_name = {
        uid: ((u.get("metadata") or {}).get("team_name") or display_name.get(uid))
        for uid, u in user_by_id.items()
    }

    # Figure out starting slot names order from league's roster_positions
    # Exclude bench/IR/taxi so indices line up with 'starters' on each roster
    starting_slots = [p for p in league.get("roster_positions", [])
                      if p not in ("BN", "IR", "TAXI")]

    rows_players: List[Dict[str, Any]] = []
    rows_teams: List[Dict[str, Any]] = []

    for r in rosters:
        owner_id = r.get("owner_id")
        roster_id = r.get("roster_id")
        starters = r.get("starters") or []
        bench = set((r.get("players") or [])) - set([s for s in starters if s])  # subtract starters
        ir = set(r.get("reserve") or [])
        taxi = set(r.get("taxi") or [])
        # Some leagues list all players only in 'players'. Make sure sets include everyone.
        all_players = set(r.get("players") or []) | set(starters) | ir | taxi
        all_players.discard(None)

        # Map each starter player_id -> its slot name using the roster order
        starter_slot_for_pid: Dict[str, str] = {}
        for idx, pid in enumerate(starters):
            if pid is None:
                continue
            slot_name = starting_slots[idx] if idx < len(starting_slots) else "STARTER"
            starter_slot_for_pid[pid] = slot_name

        def player_meta(pid: str) -> Dict[str, Any]:
            p = players_all.get(pid, {}) or {}
            full_name = p.get("full_name") or (
                ((p.get("first_name") or "") + " " + (p.get("last_name") or "")).strip()
            )
            return {
                "player_id": pid,
                "player": full_name,
                "pos": p.get("position"),
                "nfl_team": p.get("team"),
                "age": p.get("age"),
                "status": p.get("status"),
                "years_exp": p.get("years_exp"),
            }

        # Per-player rows
        for pid in sorted(all_players):
            slot_type = (
                "STARTER" if pid in starter_slot_for_pid else
                "IR" if pid in ir else
                "TAXI" if pid in taxi else
                "BENCH"
            )
            slot_label = starter_slot_for_pid.get(pid, slot_type)
            meta = player_meta(pid)
            row = {
                "league_id": league_id,
                "season": league.get("season"),
                "owner_user_id": owner_id,
                "owner_display": display_name.get(owner_id, ""),
                "team_name": team_name.get(owner_id, ""),
                "roster_id": roster_id,
                "slot_type": slot_type,
                "slot_label": slot_label,
                **meta,
            }
            rows_players.append(row)

        # Per-team summary
        settings = r.get("settings") or {}
        rows_teams.append({
            "league_id": league_id,
            "season": league.get("season"),
            "roster_id": roster_id,
            "owner_user_id": owner_id,
            "owner_display": display_name.get(owner_id, ""),
            "team_name": team_name.get(owner_id, ""),
            "wins": settings.get("wins"),
            "losses": settings.get("losses"),
            "ties": settings.get("ties"),
            "fpts": settings.get("fpts"),
            "fpts_against": settings.get("fpts_against"),
            "waiver_budget_used": settings.get("waiver_budget_used"),
            "num_players": len(all_players),
            "num_starters": sum(1 for p in starters if p),
            "num_bench": len(bench),
            "num_ir": len(ir),
            "num_taxi": len(taxi),
        })

    df_players = pd.DataFrame(rows_players).sort_values(
        ["team_name", "slot_type", "pos", "player"]
    )
    df_teams = pd.DataFrame(rows_teams).sort_values(["team_name"])

    players_out = f"sleeper_league_{league_id}_roster_players.csv"
    teams_out = f"sleeper_league_{league_id}_teams.csv"
    df_players.to_csv(players_out, index=False)
    df_teams.to_csv(teams_out, index=False)

    print(f"Wrote {players_out} ({len(df_players)} rows)")
    print(f"Wrote {teams_out} ({len(df_teams)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Export Sleeper rosters to CSV")
    ap.add_argument("--league", required=True, help="Sleeper League ID")
    args = ap.parse_args()
    main(args.league)
