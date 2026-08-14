"""Notificacoes do FUT Monitor.

Canal principal: TELEGRAM (entrega em segundos, gratuito, sem limites)
  Como ativar (uma unica vez):
  1. No Telegram, fale com @BotFather -> /newbot -> escolha nome e username.
  2. Guarde o token que ele te da (ex.: 1234567:AAAbbbCCC...).
  3. Envie qualquer mensagem ("oi") para o SEU bot recem-criado.
  4. Descubra seu chat_id: abra no navegador
       https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
     e copie o numero em "chat":{"id": ...}  (ou use o botao "Detectar chat ID"
     na tela de configuracao da interface web).
  5. Guarde nos secrets do GitHub: TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID.

Canal alternativo (fallback): WhatsApp via CallMeBot (gratuito, mas a entrega
pode atrasar alguns minutos). Secrets: WHATSAPP_PHONE e CALLMEBOT_APIKEY.

Se os dois canais estiverem configurados, envia apenas pelo Telegram.
"""

import os
import urllib.parse
import urllib.request


def _http_get(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")


def send_telegram(text, token=None, chat_id=None):
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return None  # nao configurado
    if os.environ.get("DRY_RUN"):
        print(f"[DRY_RUN] Telegram para {chat_id}:\n{text}\n")
        return True
    url = (
        f"https://api.telegram.org/bot{token}/sendMessage?"
        + urllib.parse.urlencode({"chat_id": chat_id, "text": text})
    )
    try:
        status, body = _http_get(url)
        ok = status == 200 and '"ok":true' in body.replace(" ", "")
        print(f"[notify] telegram status={status} ok={ok}")
        return ok
    except Exception as e:  # noqa: BLE001
        print(f"[notify] telegram falhou: {e}")
        return False


def send_whatsapp(text, phone=None, apikey=None):
    phone = phone or os.environ.get("WHATSAPP_PHONE", "")
    apikey = apikey or os.environ.get("CALLMEBOT_APIKEY", "")
    if not phone or not apikey:
        return None  # nao configurado
    if os.environ.get("DRY_RUN"):
        print(f"[DRY_RUN] WhatsApp para {phone}:\n{text}\n")
        return True
    url = (
        "https://api.callmebot.com/whatsapp.php?"
        + urllib.parse.urlencode({"phone": phone, "text": text, "apikey": apikey})
    )
    try:
        status, body = _http_get(url)
        ok = status == 200 and "ERROR" not in body.upper()
        print(f"[notify] whatsapp status={status} ok={ok}")
        return ok
    except Exception as e:  # noqa: BLE001
        print(f"[notify] whatsapp falhou: {e}")
        return False


def send_notification(text):
    """Envia pelo Telegram; se nao configurado, tenta WhatsApp."""
    result = send_telegram(text)
    if result is not None:
        return result
    result = send_whatsapp(text)
    if result is not None:
        return result
    print("[notify] nenhum canal configurado (Telegram ou WhatsApp) - pulando envio.")
    return False


def fmt_coins(v):
    if v is None:
        return "sem preco"
    return f"{v:,.0f}".replace(",", ".")
