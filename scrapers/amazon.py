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

def search_amazon(query: str, limit: int = 25) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.amazon.com.br/s?k={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
    }
    
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=12)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'lxml')
        items = soup.select('div[data-component-type="s-search-result"]')
        
        for item in items[:limit]:
            title_el = item.select_one('h2 span, h2 a span, a.a-text-normal span')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            
            price_whole = item.select_one('.a-price-whole')
            price_fraction = item.select_one('.a-price-fraction')
            if not price_whole:
                continue
                
            fraction_text = price_fraction.get_text(strip=True) if price_fraction else "00"
            raw_price = f"{price_whole.get_text(strip=True).replace('.', '').replace(',', '')}.{fraction_text}"
            price_val = parse_price(raw_price)
            if not price_val or price_val <= 0:
                continue
                
            link_el = item.select_one('h2 a, a.a-link-normal.s-no-outline, a.a-text-normal')
            link = ""
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                link = f"https://www.amazon.com.br{href}" if href.startswith('/') else href
                
            if not link:
                link = f"https://www.amazon.com.br/s?k={urllib.parse.quote(title)}"
                
            img_el = item.select_one('.s-image, img')
            img_url = img_el.get('src') if img_el else ""
            
            rating_el = item.select_one('span.a-icon-alt')
            rating = rating_el.get_text(strip=True).split(' ')[0] if rating_el else None
            
            results.append(ProductOffer(
                title=title,
                price=price_val,
                price_formatted=format_brl(price_val),
                store="Amazon Brasil",
                link=link,
                source="Amazon",
                image_url=img_url,
                rating=rating
            ))
    except Exception as e:
        print(f"[Scraper Amazon] Error: {e}")
        
    return results
