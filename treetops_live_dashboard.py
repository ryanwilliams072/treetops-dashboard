import requests
from pathlib import Path
from datetime import datetime
import pytz

universe_id = 751848402
place_id = 2149249364
output_file = Path("treetops_live_dashboard.html")
uk_tz = pytz.timezone("Europe/London")

def get_json(url):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def fetch_core(universe_id_value):
    data = get_json(f"https://games.roblox.com/v1/games?universeIds={universe_id_value}")
    row = (data.get("data") or [{}])[0] if data else {}
    name = str(row.get("name") or "Unknown")
    playing = int(row.get("playing") or 0)
    visits = int(row.get("visits") or 0)
    max_players = int(row.get("maxPlayers") or 0)
    created_raw = str(row.get("created") or "")
    updated_raw = str(row.get("updated") or "")
    created_date = "N/A"
    if created_raw:
        try:
            created_date = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).astimezone(uk_tz).strftime("%Y-%m-%d")
        except Exception:
            pass
    updated_clean = "N/A"
    if updated_raw:
        try:
            updated_clean = datetime.fromisoformat(updated_raw.replace("Z", "+00:00")).astimezone(uk_tz).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
    genre = str(row.get("genre") or "")
    return {"name": name, "playing": playing, "visits": visits, "max_players": max_players, "created": created_date, "updated": updated_clean, "genre": genre}

def fetch_votes(universe_id_value):
    data = get_json(f"https://games.roblox.com/v1/games/votes?universeIds={universe_id_value}")
    row = (data.get("data") or [{}])[0] if data else {}
    likes = int(row.get("upVotes") or 0)
    dislikes = int(row.get("downVotes") or 0)
    total = max(1, likes + dislikes)
    ratio = round((likes / total) * 100, 2)
    return {"likes": likes, "dislikes": dislikes, "ratio": ratio}

def fetch_icon(universe_id_value):
    data = get_json(f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_id_value}&size=150x150&format=Png&isCircular=false")
    row = (data.get("data") or [{}])[0] if data else {}
    return str(row.get("imageUrl") or "")

def fetch_servers(place_id_value, limit_count):
    data = get_json(f"https://games.roblox.com/v1/games/{place_id_value}/servers/Public?limit={limit_count}")
    servers = data.get("data") if data else []
    normalized = []
    for s in servers or []:
        normalized.append({
            "id": str(s.get("id") or ""),
            "playing": int(s.get("playing") or 0),
            "maxPlayers": int(s.get("maxPlayers") or 0),
            "ping": int(s.get("ping") or 0) if isinstance(s.get("ping"), (int, float)) else None,
            "fps": float(s.get("fps") or 0) if isinstance(s.get("fps"), (int, float)) else None
        })
    total_servers = len(normalized)
    total_players_seen = sum(s["playing"] for s in normalized)
    average_players_per_server = round(total_players_seen / total_servers, 2) if total_servers else 0.0
    busiest = max(normalized, key=lambda s: s["playing"], default=None)
    busiest_players = busiest["playing"] if busiest else 0
    return {"summary": {"total_servers": total_servers, "total_players_seen": total_players_seen, "average_players_per_server": average_players_per_server, "busiest_server_players": busiest_players}, "list": normalized}

def humanize(n):
    if n is None:
        return "N/A"
    n = int(n)
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1000:.1f}k"
    if n < 1_000_000_000:
        return f"{n/1_000_000:.1f}M"
    return f"{n/1_000_000_000:.1f}B"

def build_html(payload):
    generated_at = datetime.now(uk_tz).strftime("%Y-%m-%d %H:%M %Z")
    game_url = "https://www.roblox.com/games/2149249364/Tree-Tops-Theme-Park"
    name = payload["core"]["name"]
    icon_url = payload["icon_url"]
    likes = payload["votes"]["likes"]
    dislikes = payload["votes"]["dislikes"]
    like_ratio = payload["votes"]["ratio"]
    playing = payload["core"]["playing"]
    visits = payload["core"]["visits"]
    max_players = payload["core"]["max_players"]
    created = payload["core"]["created"]
    updated = payload["core"]["updated"]
    genre = payload["core"]["genre"]
    servers_summary = payload["servers"]["summary"]
    servers_list = payload["servers"]["list"]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{name} — Live Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="300">
  <style>
    :root {{
      --bg1:#2c2c2c; --bg2:#444; --card:#3a3a3a; --text:#fff; --muted:#ccc; --muted2:#aaa;
      --green:#00ff6a; --orange:#F7941D; --blue:#0071CE; --purple:#92278F; --teal:#009E9B;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; padding:20px; font-family:Arial, Helvetica, sans-serif; color:var(--text); background:linear-gradient(135deg,var(--bg1),var(--bg2)); }}
    .wrap {{ max-width:1100px; margin:0 auto; }}
    header {{ display:grid; grid-template-columns:72px 1fr auto; gap:16px; align-items:center; }}
    .icon {{ width:72px; height:72px; border-radius:12px; background:#222; overflow:hidden; }}
    .icon img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    h1 {{ margin:0; font-size:2rem; }}
    .sub {{ color:var(--muted2); font-size:0.95rem; margin-top:6px; }}
    .actions a {{ display:inline-block; padding:10px 14px; background:var(--teal); color:#fff; text-decoration:none; border-radius:8px; font-weight:bold; }}
    #clock {{ text-align:center; color:var(--muted); margin:10px 0 24px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-bottom:22px; }}
    .card {{ background:var(--card); border-left:8px solid #ccc; border-radius:10px; padding:16px; box-shadow:0 4px 12px rgba(0,0,0,0.35); }}
    .green {{ border-left-color:var(--green); box-shadow:0 0 12px rgba(0,255,106,0.25); }}
    .orange {{ border-left-color:var(--orange); }}
    .blue {{ border-left-color:var(--blue); }}
    .purple {{ border-left-color:var(--purple); }}
    .metric-name {{ color:#ddd; font-size:0.95rem; margin-bottom:6px; }}
    .metric-value {{ font-size:2rem; font-weight:bold; }}
    .row {{ margin-top:8px; color:#e0e0e0; font-size:0.95rem; }}
    .ratio-bar {{ height:10px; background:#222; border-radius:6px; overflow:hidden; margin-top:10px; }}
    .ratio-fill {{ height:100%; background:var(--green); width:{like_ratio}%; transition:width .6s ease; }}
    .section-title {{ margin:26px 0 12px 0; font-size:1.2rem; }}
    table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:10px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.35); table-layout:fixed; }}
    thead tr {{ background:#2f2f2f; }}
    th,td {{ padding:10px 12px; text-align:left; font-size:0.95rem; }}
    tbody tr:nth-child(even) {{ background:#353535; }}
    .id {{ font-family:monospace; word-break:break-all; white-space:normal; }}
    .footer {{ text-align:center; color:var(--muted2); font-size:0.9rem; margin-top:20px; }}
  </style>
  <script>
    function tick() {{
      const el = document.getElementById("clock");
      if (el) el.textContent = new Date().toLocaleString("en-GB", {{ timeZone: "Europe/London" }});
    }}
    setInterval(tick, 1000);
    window.onload = tick;
  </script>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="icon">{f'<img src="{icon_url}" alt="icon">' if icon_url else ""}</div>
      <div>
        <h1>{name} — Live Dashboard</h1>
        <div class="sub">Genre: {genre or "N/A"} • Created: {created} • Updated: {updated}</div>
      </div>
      <div class="actions"><a href="{game_url}" target="_blank" rel="noopener">Open Game</a></div>
    </header>

    <div id="clock"></div>
    <div class="sub" style="text-align:center;">Last updated: {generated_at}</div>

    <div class="grid">
      <div class="card green">
        <div class="metric-name">Players Online</div>
        <div class="metric-value">{playing}</div>
        <div class="row">Max Players: {max_players}</div>
      </div>
      <div class="card orange">
        <div class="metric-name">Likes</div>
        <div class="metric-value">{likes}</div>
        <div class="row">Dislikes: {dislikes}</div>
        <div class="row">Like Ratio: {like_ratio}%</div>
        <div class="ratio-bar"><div class="ratio-fill"></div></div>
      </div>
      <div class="card purple">
        <div class="metric-name">Visits</div>
        <div class="metric-value">{humanize(visits)}</div>
      </div>
      <div class="card blue">
        <div class="metric-name">Servers</div>
        <div class="row">Total Servers: {servers_summary["total_servers"]}</div>
        <div class="row">Players Across Listed Servers: {servers_summary["total_players_seen"]}</div>
        <div class="row">Average Players per Server: {servers_summary["average_players_per_server"]}</div>
        <div class="row">Busiest Server Players: {servers_summary["busiest_server_players"]}</div>
      </div>
    </div>

    <div class="section-title">Active Public Servers</div>
    <div style="overflow-x:auto;">
      <table>
        <colgroup>
          <col style="width:120px;">
          <col style="width:120px;">
          <col style="width:140px;">
          <col style="width:auto;">
        </colgroup>
        <thead>
          <tr><th>Players</th><th>Capacity</th><th>Ping</th><th>Server Id</th></tr>
        </thead>
        <tbody>
          {''.join(f"<tr><td>{s['playing']}</td><td>{s['maxPlayers']}</td><td>{(str(s['ping'])+' ms') if s['ping'] is not None else 'N/A'}</td><td class='id'>{s['id']}</td></tr>" for s in servers_list[:50])}
        </tbody>
      </table>
    </div>

    <div class="footer">Data refreshes every 5 minutes. Times shown in UK local time.</div>
  </div>
</body>
</html>"""
    return html

def main():
    core = fetch_core(universe_id)
    votes = fetch_votes(universe_id)
    icon_url = fetch_icon(universe_id)
    servers = fetch_servers(place_id, 100)
    html = build_html({"core": core, "votes": votes, "icon_url": icon_url, "servers": servers})
    output_file.write_text(html, encoding="utf-8")
    print(str(output_file.resolve()))

if __name__ == "__main__":
    main()
