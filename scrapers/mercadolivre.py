import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from models import ProductOffer

# O Mercado Livre bloqueia requisições HTTP diretas e navegadores headless
# (página "suspicious_traffic" pedindo login). Um Chrome/Edge real, com janela
# (posicionada fora da tela), passa normalmente. Por isso usamos Playwright aqui.
BROWSER_CHANNELS = ["chrome", "msedge"]


def format_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _read_price(container) -> Optional[float]:
    if container is None:
        return None
    frac = container.select_one('.andes-money-amount__fraction')
    if not frac:
        return None
    cents = container.select_one('.andes-money-amount__cents')
    try:
        value = float(frac.get_text(strip=True).replace('.', ''))
        if cents:
            value += float(cents.get_text(strip=True)) / 100
        return value
    except ValueError:
        return None


def _parse_cards(html: str, limit: int) -> List[ProductOffer]:
    soup = BeautifulSoup(html, 'lxml')
    results: List[ProductOffer] = []
    seen = set()

    for card in soup.select('div.poly-card, li.ui-search-layout__item'):
        if len(results) >= limit:
            break

        title_el = card.select_one('.poly-component__title, .ui-search-item__title, h3, h2')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        link_el = card.select_one('a.poly-component__title, a.ui-search-link, a[href]')
        link = link_el.get('href', '') if link_el else ''
        if not link.startswith('http'):
            continue
        link = link.split('#')[0]
        if link in seen:
            continue

        # Preço atual (o preço riscado "de" fica dentro de <s>)
        current = card.select_one('.poly-price__current') or card.select_one('.ui-search-price__second-line')
        price = _read_price(current)
        if price is None:
            for amount in card.select('.andes-money-amount'):
                if amount.name != 's' and amount.find_parent('s') is None:
                    price = _read_price(amount)
                    break
        if not price or price <= 0:
            continue

        original = _read_price(card.select_one('s.andes-money-amount, .andes-money-amount--previous'))
        discount = None
        if original and original > price:
            discount = int(round((original - price) / original * 100))

        seller_el = card.select_one('.poly-component__seller, .ui-search-official-store-label')
        seller = seller_el.get_text(strip=True) if seller_el else ''

        img_el = card.select_one('img')
        img = ''
        if img_el:
            img = img_el.get('data-src') or img_el.get('src') or ''
            if img.startswith('data:'):
                img = ''

        seen.add(link)
        results.append(ProductOffer(
            title=title,
            price=price,
            price_formatted=format_brl(price),
            store="Mercado Livre",
            link=link,
            source=f"Mercado Livre{(' · ' + seller) if seller else ''}",
            image_url=img,
            original_price=original,
            discount_pct=discount,
        ))
    return results


def search_mercadolivre(query: str, limit: int = 20) -> List[ProductOffer]:
    slug = urllib.parse.quote(re.sub(r'\s+', '-', query.strip().lower()))
    url = f"https://lista.mercadolivre.com.br/{slug}"

    with sync_playwright() as p:
        browser = None
        for channel in BROWSER_CHANNELS:
            try:
                browser = p.chromium.launch(
                    channel=channel,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled",
                          "--window-position=-2400,0", "--window-size=1280,900"],
                )
                break
            except Exception:
                continue
        if browser is None:
            print("[Mercado Livre] Nenhum Chrome/Edge instalado encontrado.")
            return []

        try:
            ctx = browser.new_context(locale="pt-BR", timezone_id="America/Sao_Paulo")
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            try:
                page.wait_for_selector("div.poly-card, li.ui-search-layout__item", timeout=8000)
            except Exception:
                print(f"[Mercado Livre] Nenhum anúncio carregou (url final: {page.url})")
                return []
            # Rola a página para carregar as imagens (lazy load)
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(600)
            return _parse_cards(page.content(), limit)
        except Exception as e:
            print(f"[Mercado Livre] Erro: {e}")
            return []
        finally:
            browser.close()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    q = " ".join(sys.argv[1:]) or "controle ps5 dualsense"
    res = search_mercadolivre(q)
    print(f"Mercado Livre: {len(res)} ofertas reais")
    for r in res[:10]:
        print(f"  {r.price_formatted:>12} | {r.title[:60]} | {r.link[:60]}")
