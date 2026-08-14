"""Notificacao por WhatsApp via CallMeBot (gratuito para uso pessoal).

Como ativar (uma unica vez):
1. Abra https://wa.me/34644872157 (numero atual: +34 644 87 21 57).
2. Envie pelo WhatsApp a mensagem: "I allow callmebot to send me messages"
3. Aguarde a resposta com sua API key (ex.: "Your APIKEY is 123456").
4. Guarde seu telefone (formato +5511999999999) e a apikey nos secrets do GitHub.

Docs: https://www.callmebot.com/blog/free-api-whatsapp-messages/
"""

import os
import urllib.parse
import urllib.request


def send_whatsapp(text, phone=None, apikey=None, timeout=30):
    phone = phone or os.environ.get("WHATSAPP_PHONE", "")
    apikey = apikey or os.environ.get("CALLMEBOT_APIKEY", "")
    if os.environ.get("DRY_RUN"):
        print(f"[DRY_RUN] WhatsApp para {phone or '(sem numero)'}:\n{text}\n")
        return True
    if not phone or not apikey:
        print("[notify] WHATSAPP_PHONE/CALLMEBOT_APIKEY nao configurados - pulando envio.")
        return False
    url = (
        "https://api.callmebot.com/whatsapp.php?"
        + urllib.parse.urlencode({"phone": phone, "text": text, "apikey": apikey})
    )
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="ignore")
            ok = r.status == 200 and "ERROR" not in body.upper()
            print(f"[notify] status={r.status} ok={ok}")
            return ok
    except Exception as e:  # noqa: BLE001
        print(f"[notify] falha no envio: {e}")
        return False


def fmt_coins(v):
    if v is None:
        return "sem preco"
    return f"{v:,.0f}".replace(",", ".")
