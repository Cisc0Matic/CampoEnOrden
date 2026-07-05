import logging
import re
import time
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# Simple in-process time-based cache — good enough for serverless (warm instance)
_cache: dict = {}
_CACHE_SECS = 1800  # 30 minutes


def _cached(key: str, fn):
    now = time.monotonic()
    if key in _cache:
        value, expires = _cache[key]
        if now < expires:
            return value
    value = fn()
    if value:
        _cache[key] = (value, now + _CACHE_SECS)
    return value


# ── Dollar rates ──────────────────────────────────────────────────────────────

_DOLAR_LABELS = {
    'oficial': 'Oficial',
    'blue': 'Blue (informal)',
    'bolsa': 'MEP / Bolsa',
    'exportacion': 'Exportación',
}


def get_dolar_text() -> str:
    def fetch():
        try:
            resp = requests.get('https://dolarapi.com/v1/dolares', timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = ['💵 *Dólar — Argentina*\n']
            for item in data:
                casa = item.get('casa', '')
                if casa not in _DOLAR_LABELS:
                    continue
                nombre = _DOLAR_LABELS[casa]
                compra = item.get('compra')
                venta = item.get('venta')
                if compra and venta:
                    lines.append(f'*{nombre}:* ${compra:,.0f} compra · ${venta:,.0f} venta')
            if len(lines) < 2:
                return None
            lines.append(f'\n_Actualizado: {datetime.now().strftime("%d/%m %H:%M")}_')
            return '\n'.join(lines)
        except Exception as e:
            logger.warning(f'dolarapi fetch error: {e}')
            return None

    return _cached('dolar', fetch) or (
        '⚠️ No se pudo obtener la cotización del dólar.\n'
        'Intentá de nuevo en unos minutos.'
    )


# ── Grain prices (BCR) ────────────────────────────────────────────────────────

_BCR_URL = (
    'https://www.bcr.com.ar/es/mercados/mercado-de-granos/cotizaciones/'
    'cotizaciones-locales/mercado-fisico-de-rosario/precios-4419'
)

# Crops to look for, in display order
_CULTIVOS = [
    ('Soja', ['soja']),
    ('Maíz', ['maíz', 'maiz']),
    ('Trigo', ['trigo']),
    ('Girasol', ['girasol']),
    ('Sorgo', ['sorgo']),
]

# u$s 205, u$s 178.50
_USD_RE = re.compile(r'u\$s\s*([\d.,]+)', re.IGNORECASE)
# $460,000 or $460.000 (ARS large numbers)
_ARS_RE = re.compile(r'\$\s*([\d]{3,}[.,]\d+)')


def _clean_num(s: str) -> str:
    s = s.strip()
    # Argentine format: 460.000,00 → remove dots, comma = decimal
    # USD format: 205.50 → keep as is
    if '.' in s and ',' in s:
        if s.index('.') < s.index(','):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s and '.' not in s:
        s = s.replace(',', '.')
    # Strip trailing zeros after decimal
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def _parse_bcr_html(html: str) -> list[tuple]:
    results = []
    seen = set()
    lower = html.lower()
    for display, keywords in _CULTIVOS:
        if display in seen:
            continue
        for kw in keywords:
            idx = lower.find(kw)
            if idx < 0:
                continue
            # Search in a window around the keyword
            snippet = html[max(0, idx - 50): idx + 500]
            usd = _USD_RE.search(snippet)
            if usd:
                results.append((display, _clean_num(usd.group(1)), 'USD'))
                seen.add(display)
                break
            ars = _ARS_RE.search(snippet)
            if ars:
                results.append((display, _clean_num(ars.group(1)), 'ARS'))
                seen.add(display)
                break
    return results


def get_precios_cereales_text() -> str:
    def fetch():
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/126.0 Safari/537.36'
                ),
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            resp = requests.get(_BCR_URL, headers=headers, timeout=15)
            resp.raise_for_status()
            prices = _parse_bcr_html(resp.text)
            if not prices:
                logger.warning('BCR scrape returned no prices — page structure may have changed')
                return None
            lines = ['🌾 *Precios de Granos — Rosario*\n']
            for cultivo, precio, moneda in prices:
                if moneda == 'USD':
                    lines.append(f'*{cultivo}:* u$s {precio}/tn')
                else:
                    lines.append(f'*{cultivo}:* ${precio}/tn')
            lines.append(f'\n_Fuente: BCR · {datetime.now().strftime("%d/%m %H:%M")}_')
            return '\n'.join(lines)
        except Exception as e:
            logger.warning(f'BCR prices fetch error: {e}')
            return None

    return _cached('cereales', fetch) or (
        '🌾 *Precios de Granos*\n\n'
        'No se pudo obtener los precios en este momento.\n\n'
        'Consultá en: bcr.com.ar → Mercados → Granos'
    )
