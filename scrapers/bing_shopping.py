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

def search_bing_shopping(query: str, limit: int = 30) -> List[ProductOffer]:
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.bing.com/shop?q={encoded_query}&setmkt=pt-BR&setlang=pt-BR&cc=BR"
    
    try:
        cookies = {'_EDGE_S': 'mkt=pt-br', 'SRCHHPGUSR': 'WTS=638&NRSLT=50'}
        resp = requests.get(url, cookies=cookies, impersonate="chrome124", timeout=12)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'lxml')
        cards = soup.select('div.br-gOffCard, div.br-offCard, div.br-card, li.br-item, div.br-standardCard, div[class*="OffCard"]')
        
        seen_titles = set()
        for card in cards:
            if len(results) >= limit:
                break
                
            text = card.get_text(" ", strip=True)
            if 'R$' not in text:
                continue
                
            # Title
            span_title = card.select_one('.br-offTtl span[title], span[title], a[title]')
            if span_title and span_title.get('title'):
                title = span_title.get('title').strip()
            else:
                t_el = card.select_one('.br-offTtl, .br-title, h3, a.br-offTitle, .br-sellerFocusTitle')
                title = t_el.get_text(strip=True) if t_el else ""
            if not title or len(title) < 5:
                continue
                
            # Clean duplicate repetitive words in Bing titles if any
            if len(title) > 30 and title[:15] == title[15:30]:
                title = title[:len(title)//2]
                
            # Price
            p_el = card.select_one('.br-price, .br-offPrice')
            price_text = p_el.get_text(strip=True) if p_el else text
            price_match = re.search(r'R\$\s*([\d.]+,\d{2}|\d+)', price_text)
            if not price_match:
                continue
            price_val = parse_price(price_match.group(0))
            if not price_val or price_val <= 0:
                continue
                
            # Seller / Store
            s_el = card.select_one('.br-offSlrTxt, .br-offSlr, .br-seller, .seller, .br-sellers, .br-sellerName')
            seller = s_el.get_text(strip=True) if s_el else ""
            if not seller or seller.lower() == 'anúncio':
                seller_match = re.search(r'(Mercado Livre|Amazon BR|Amazon|KaBuM!|KaBuM|Shopee|Magalu|Magazine Luiza|Casas Bahia|Ponto|Carrefour|Terabyte|Pichau|AliExpress)', text, re.IGNORECASE)
                seller = seller_match.group(0) if seller_match else "Loja Online"
                
            # Normalizar nome da loja para bater com os filtros da interface
            seller_clean = seller
            if re.search(r'amazon', seller, re.IGNORECASE):
                seller_clean = "Amazon Brasil"
            elif re.search(r'mercado\s*livre', seller, re.IGNORECASE):
                seller_clean = "Mercado Livre"
            elif re.search(r'kabum', seller, re.IGNORECASE):
                seller_clean = "KaBuM!"
            elif re.search(r'magalu|magazine', seller, re.IGNORECASE):
                seller_clean = "Magalu"

            # Link
            link = ""
            for a in card.select('a.br-offLink, a[href]'):
                href = a.get('href', '')
                if href and not href.startswith('javascript'):
                    link = f"https://www.bing.com{href}" if href.startswith('/') else href
                    # Se tiver URL de destino codificada no parâmetro u=, decodifica para levar direto à loja
                    if 'u=' in href:
                        import base64
                        u_match = re.search(r'[?&]u=([^&]+)', href)
                        if u_match:
                            try:
                                padded = u_match.group(1) + '=='
                                decoded = urllib.parse.unquote(base64.b64decode(padded).decode('utf-8', errors='ignore'))
                                if decoded.startswith('http'):
                                    link = decoded
                            except Exception:
                                pass
                    break
                    
            # Image
            img_el = card.select_one('img.rms_img, img')
            img = ""
            if img_el:
                img = img_el.get('src') or img_el.get('data-src') or ""
                if img.startswith('data:'):
                    img = ""
            
            key = (title[:30].lower(), round(price_val, 0))
            if key in seen_titles:
                continue
            seen_titles.add(key)
            
            results.append(ProductOffer(
                title=title,
                price=price_val,
                price_formatted=format_brl(price_val),
                store=seller_clean,
                link=link,
                source="Shopping MultiLojas",
                image_url=img
            ))
    except Exception as e:
        print(f"[Scraper Bing Shop] Error: {e}")
        
    return results

if __name__ == '__main__':
    res = search_bing_shopping("controle ps5 dualsense")
    print(f"Shopping MultiLojas total: {len(res)}")
    for r in res[:5]:
        print(f"  • [{r.store}] {r.title[:40]} -> {r.price_formatted}")

