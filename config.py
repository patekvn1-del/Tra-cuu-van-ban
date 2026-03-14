import os

# ── Railway đọc từ biến môi trường ──────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

SOAP_URL       = "https://ws.vbpl.vn/vbqppl.asmx"
SOAP_NAMESPACE = "http://tempuri.org/"
VBPL_BASE      = "https://vbpl.vn"
REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

DIA_PHUONG = {
    "bariavungtau": "🛢️ Bà Rịa - Vũng Tàu",
    "binhdung":     "🏭 Bình Dương",
    "tphcm":        "🏙️ TP. Hồ Chí Minh",
}

VBPL_DOMAIN = {
    "bariavungtau": "https://vbpl.vn/bariavungtau",
    "binhdung":     "https://vbpl.vn/binhdung",
    "tphcm":        "https://vbpl.vn/tphcm",
}
