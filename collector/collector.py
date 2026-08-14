"""FUT Monitor - coletor de precos do fut.gg.

Executado pelo GitHub Actions (ou localmente). Fluxo:
1. Le a watchlist em data/players.json
2. Busca o mapa de precos atual (CDN publico do fut.gg)
3. Garante metadados de cada carta (scrape unico da pagina do jogador)
4. Registra historico em data/history/<cardId>.json
5. Avalia alertas e envia WhatsApp (CallMeBot)
6. Gera data/summary.json para a interface web

Env vars:
  PLATFORM             ps5 (console, padrao) ou pc
  TELEGRAM_BOT_TOKEN   token do bot (canal principal - entrega em segundos)
  TELEGRAM_CHAT_ID     seu chat id no Telegram
  WHATSAPP_PHONE       +5511999999999 (fallback via CallMeBot)
  CALLMEBOT_APIKEY     chave do CallMeBot (fallback)
  DRY_RUN              se definido, imprime notificacoes em vez de enviar
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import futgg  # noqa: E402
from notify import send_notification, fmt_coins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HISTORY_DIR = os.path.join(DATA, "history")
META_DIR = os.path.join(DATA, "meta")
MAX_POINTS = 6000  # ~4 meses em intervalos de 30 min


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def ensure_meta(player, core, playstyles_map):
    card_id = player["cardId"]
    path = os.path.join(META_DIR, f"{card_id}.json")
    meta = load_json(path, None)
    if meta and meta.get("name"):
        return meta
    try:
        print(f"[meta] buscando metadados de {player['url']}")
        meta = futgg.scrape_player_meta(player["url"], core=core, playstyles_map=playstyles_map)
        save_json(path, meta)
        return meta
    except Exception as e:  # noqa: BLE001
        print(f"[meta] falha ({card_id}): {e}")
        return meta or {"cardId": card_id, "eaId": player.get("eaId"), "name": None}


def append_history(card_id, ts, price):
    path = os.path.join(HISTORY_DIR, f"{card_id}.json")
    hist = load_json(path, {"cardId": card_id, "points": []})
    pts = hist["points"]
    # evita duplicar se o preco publicado ainda e o mesmo timestamp
    if pts and pts[-1][0] == ts:
        pts[-1][1] = price
    else:
        pts.append([ts, price])
    if len(pts) > MAX_POINTS:
        hist["points"] = pts[-MAX_POINTS:]
    save_json(path, hist)
    return hist


def price_at(hist, seconds_ago, now):
    """Preco valido mais recente com pelo menos `seconds_ago` de idade."""
    target = now - seconds_ago
    best = None
    for ts, price in hist["points"]:
        if ts <= target and price:
            best = price
    return best


def check_alert(player, price, prev_price):
    """Retorna texto do alerta ou None. Modos:
    - every: notifica em toda checagem com o valor atual
    - below: notifica quando o preco CRUZA para baixo do alvo
    - above: notifica quando o preco CRUZA para cima do alvo
    - off:   nunca notifica
    """
    mode = player.get("alertMode", "off")
    target = player.get("targetPrice")
    name = player.get("_name") or f"Carta {player['cardId']}"
    url = player.get("url", "")

    if not price:
        return None
    if mode == "every":
        return f"⚽ {name}: {fmt_coins(price)} moedas\n{url}"
    if mode in ("below", "above") and target:
        crossed = False
        if mode == "below":
            crossed = price <= target and (prev_price is None or prev_price > target)
            arrow = "\U0001f4c9 caiu para"
        else:
            crossed = price >= target and (prev_price is None or prev_price < target)
            arrow = "\U0001f4c8 subiu para"
        if crossed:
            return (
                f"\U0001f6a8 ALERTA DE PRECO\n⚽ {name} {arrow} "
                f"{fmt_coins(price)} moedas (alvo: {fmt_coins(target)})\n{url}"
            )
    return None


def main():
    platform = os.environ.get("PLATFORM", "ps5")
    now = int(time.time())

    cfg_path = os.path.join(DATA, "players.json")
    cfg = load_json(cfg_path, {"settings": {}, "players": []})
    players = cfg.get("players", [])

    # normaliza entradas que so tem o link
    changed_cfg = False
    for p in players:
        if not p.get("cardId"):
            ids = futgg.parse_player_url(p.get("url", ""))
            if ids:
                p["eaId"], p["cardId"] = ids
                changed_cfg = True
    players = [p for p in players if p.get("cardId")]

    if not players:
        print("Nenhum jogador na watchlist. Adicione links em data/players.json")
        save_json(os.path.join(DATA, "summary.json"), {
            "generatedAt": now, "platform": platform, "players": [],
        })
        return

    manifest = futgg.get_manifest()
    price_map = futgg.get_price_map(platform, manifest)
    published_at = futgg.get_prices_published_at(manifest, platform) or now
    print(f"[precos] {len(price_map)} cartas | publicado ha {(now - published_at) // 60} min")

    core = None
    playstyles_map = None
    need_meta = [p for p in players if not load_json(
        os.path.join(META_DIR, f"{p['cardId']}.json"), {}).get("name")]
    if need_meta:
        try:
            core = futgg.get_core_data(manifest)
            playstyles_map = futgg.get_playstyles_map(manifest)
        except Exception as e:  # noqa: BLE001
            print(f"[meta] core data indisponivel: {e}")

    summary_players = []
    alerts = []
    for p in players:
        meta = ensure_meta(p, core, playstyles_map)
        p["_name"] = meta.get("name")
        price = price_map.get(p["cardId"]) or None
        hist = append_history(p["cardId"], published_at, price or 0)
        prev = None
        valid = [pt for pt in hist["points"][:-1] if pt[1]]
        if valid:
            prev = valid[-1][1]

        alert = check_alert(p, price, prev)
        if alert:
            alerts.append(alert)

        p24 = price_at(hist, 24 * 3600, now)
        summary_players.append({
            "cardId": p["cardId"],
            "eaId": p.get("eaId"),
            "url": p.get("url"),
            "name": meta.get("name"),
            "rating": meta.get("overall"),
            "position": meta.get("positionName"),
            "rarityName": meta.get("rarityName"),
            "cardImageUrl": meta.get("cardImageUrl"),
            "price": price,
            "prevPrice": prev,
            "price24hAgo": p24,
            "change24h": (price - p24) if (price and p24) else None,
            "targetPrice": p.get("targetPrice"),
            "alertMode": p.get("alertMode", "off"),
            "extinct": price is None,
        })

    for text in alerts:
        send_notification(text)

    save_json(os.path.join(DATA, "summary.json"), {
        "generatedAt": now,
        "pricesPublishedAt": published_at,
        "platform": platform,
        "players": summary_players,
    })

    if changed_cfg:
        cfg["players"] = [
            {k: v for k, v in p.items() if not k.startswith("_")} for p in players
        ]
        save_json(cfg_path, cfg)

    print(f"[ok] {len(players)} jogador(es), {len(alerts)} alerta(s)")


if __name__ == "__main__":
    main()
