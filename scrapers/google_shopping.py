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

def search_google_shopping(query: str, limit: int = 15) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?tbm=shop&q={encoded_query}&hl=pt-BR&gl=br"
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=12)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'lxml')
        cards = soup.select('.sh-dgr__grid-result, .sh-dlr__list-result, div[data-docid]')
        
        for card in cards[:limit]:
            # Title
            title_el = card.select_one('h3, h4, .tAxLfb, .Xjkr3b')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            
            # Price
            price_el = card.select_one('.a8Pemb, .OFFNJ, span[class*="price"], .kHssdc')
            if not price_el:
                continue
            price_val = parse_price(price_el.get_text(strip=True))
            if not price_val or price_val <= 0:
                continue
                
            # Merchant / Store
            store_el = card.select_one('.aULzUe, .IuHnof, .eaLbx, .hBDAFd')
            store = store_el.get_text(strip=True) if store_el else "Google Shopping"
            
            # Link
            link_el = card.select_one('a')
            link = link_el.get('href', '') if link_el else ''
            if link and link.startswith('/url?q='):
                link = link.split('/url?q=')[1].split('&')[0]
                link = urllib.parse.unquote(link)
            elif link and link.startswith('/'):
                link = f"https://www.google.com{link}"
                
            # Image
            img_el = card.select_one('img')
            img_url = img_el.get('src') or img_el.get('data-src') or "" if img_el else ""
            
            results.append(ProductOffer(
                title=title,
                price=price_val,
                price_formatted=format_brl(price_val),
                store=store,
                link=link,
                source="Google Shopping",
                image_url=img_url
            ))
    except Exception as e:
        print(f"[Scraper Google Shopping] Error: {e}")
        
    return results

