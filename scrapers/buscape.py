import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import urllib.parse
from typing import List, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
from models import ProductOffer

def parse_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    cleaned = re.sub(r'[^\d,.]', '', str(price_str))
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def format_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def search_buscape_zoom(query: str, limit: int = 40) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.zoom.com.br/search?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9',
    }
    
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=12)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'lxml')
        cards = soup.select('div[class*="ProductCard_ProductCard_Inner__"], [data-testid="product-card"], div[class*="ProductCard_"]')
        
        seen_keys = set()
        for card in cards:
            if len(results) >= limit:
                break
                
            t_el = card.select_one('h2, [data-testid="product-card::name"], [class*="ProductCard_ProductCard_Name__"], [class*="Text_Text__"]')
            title = t_el.get_text(strip=True) if t_el else ""
            if not title or len(title) < 5:
                continue
                
            p_el = card.select_one('[data-testid="product-card::price"], [class*="Price_Value__"], [class*="Price_price__"]')
            if not p_el:
                continue
            price_val = parse_price(p_el.get_text(strip=True))
            if not price_val or price_val <= 0:
                continue
                
            s_el = card.select_one('[data-testid="product-card::merchant"], [class*="Merchant"], span[class*="Merchant"]')
            store = s_el.get_text(strip=True) if s_el else "Zoom / Lojas Parceiras"
            if store.lower().startswith('via '):
                store = store[4:].strip()
            if store == "Diversas Lojas" or not store:
                store = "Zoom / Multilojas"
                
            # Extrair link garantido
            link = ""
            for a in card.select('a[href]'):
                href = a.get('href', '').strip()
                if href and not href.startswith('javascript'):
                    link = f"https://www.zoom.com.br{href}" if href.startswith('/') else href
                    break
                    
            if not link:
                link = f"https://www.zoom.com.br/search?q={urllib.parse.quote(title)}"
                
            img_el = card.select_one('img')
            img = img_el.get('src') or img_el.get('data-src') if img_el else ""
            
            key = (title[:25].lower(), round(price_val, 0), store.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            results.append(ProductOffer(
                title=title,
                price=price_val,
                price_formatted=format_brl(price_val),
                store=store,
                link=link,
                source="Zoom / Buscapé",
                image_url=img
            ))
    except Exception as e:
        print(f"[Scraper Zoom] Error: {e}")
        
    return results
