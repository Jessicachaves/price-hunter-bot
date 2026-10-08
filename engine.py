import sys
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from models import ProductOffer

from scrapers.kabum import search_kabum
from scrapers.buscape import search_buscape_zoom
from scrapers.bing_shopping import search_bing_shopping
from scrapers.amazon import search_amazon
from scrapers.mercadolivre import search_mercadolivre
from relevance import filter_relevant

def format_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

class ComparisonEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=6)

    def search_all_sync(self, query: str) -> Dict[str, Any]:
        """
        Executa buscas paralelas em múltiplas lojas e motores de busca do Brasil
        e calcula métricas completas de comparação de preços.
        """
        start_time = time.time()
        
        tasks = {
            "Mercado Livre": lambda: search_mercadolivre(query, limit=15),
            "KaBuM!": lambda: search_kabum(query, limit=20),
            "Zoom / Buscapé": lambda: search_buscape_zoom(query, limit=35),
            "Shopping MultiLojas": lambda: search_bing_shopping(query, limit=35),
            "Amazon Brasil": lambda: search_amazon(query, limit=20),
        }

        future_to_source = {
            self.executor.submit(func): source_name 
            for source_name, func in tasks.items()
        }

        all_offers: List[ProductOffer] = []
        source_counts = {}

        try:
            for future in as_completed(future_to_source, timeout=30):
                source_name = future_to_source[future]
                try:
                    offers = future.result()
                    source_counts[source_name] = len(offers)
                    all_offers.extend(offers)
                except Exception as e:
                    print(f"[{source_name}] falhou: {e}")
                    source_counts[source_name] = 0
        except TimeoutError:
            for future, source_name in future_to_source.items():
                if source_name not in source_counts:
                    print(f"[{source_name}] demorou demais e foi ignorada")
                    source_counts[source_name] = 0

        # Filtra preços zerados ou inválidos (< R$ 1,00)
        valid_offers = [o for o in all_offers if o.price and o.price >= 1.0]

        if not valid_offers:
            return {
                "query": query,
                "total_found": 0,
                "cheapest": None,
                "most_expensive": None,
                "average_price": 0,
                "average_price_formatted": "R$ 0,00",
                "max_savings": 0,
                "max_savings_formatted": "R$ 0,00",
                "savings_vs_avg": 0,
                "savings_vs_avg_formatted": "R$ 0,00",
                "offers": [],
                "source_counts": source_counts,
                "search_time_sec": round(time.time() - start_time, 2)
            }

        # Desduplicação inteligente
        seen_keys = set()
        unique_offers: List[ProductOffer] = []
        for offer in valid_offers:
            title_clean = "".join(filter(str.isalnum, offer.title[:25].lower()))
            price_bucket = round(offer.price, 0)
            key = (title_clean, price_bucket, offer.store.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_offers.append(offer)

        # Filtro de relevância: descarta peças, capas, grips e acessórios indesejados
        relevant_offers, filtered_out = filter_relevant(unique_offers, query)
        if relevant_offers:
            unique_offers = relevant_offers

        # Ordenar do menor para o maior preço
        unique_offers.sort(key=lambda x: x.price)

        cheapest = unique_offers[0]
        most_expensive = unique_offers[-1]
        
        prices = [o.price for o in unique_offers]
        avg_price = sum(prices) / len(prices)
        savings = most_expensive.price - cheapest.price
        savings_vs_avg = max(0.0, avg_price - cheapest.price)

        # Descontos relativos
        for o in unique_offers:
            if most_expensive.price > 0 and o.price < most_expensive.price:
                diff = most_expensive.price - o.price
                o.discount_pct = int((diff / most_expensive.price) * 100)
            else:
                o.discount_pct = 0

        return {
            "query": query,
            "total_found": len(unique_offers),
            "cheapest": cheapest,
            "most_expensive": most_expensive,
            "average_price": avg_price,
            "average_price_formatted": format_brl(avg_price),
            "max_savings": savings,
            "max_savings_formatted": format_brl(savings),
            "savings_vs_avg": savings_vs_avg,
            "savings_vs_avg_formatted": format_brl(savings_vs_avg),
            "offers": unique_offers,
            "source_counts": source_counts,
            "search_time_sec": round(time.time() - start_time, 2)
        }

engine = ComparisonEngine()
