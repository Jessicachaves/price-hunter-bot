import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine import engine

def main():
    if len(sys.argv) < 2:
        query = input("Digite o produto que deseja pesquisar: ").strip()
    else:
        query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Nenhum termo informado.")
        return

    print(f"\n==================================================")
    print(f"Pesquisando '{query}' nas lojas...")
    print(f"==================================================")

    res = engine.search_all_sync(query)

    if res['total_found'] == 0:
        print("Nenhuma oferta encontrada para essa busca.")
        return

    print(f"\nTotal: {res['total_found']} ofertas encontradas em {res['search_time_sec']}s\n")

    cheapest = res['cheapest']
    print(f"MELHOR PRECO:")
    print(f"   Produto: {cheapest.title}")
    print(f"   Preco:   {cheapest.price_formatted}")
    print(f"   Loja:    {cheapest.store}")
    print(f"   Link:    {cheapest.link}")
    
    if res['savings_vs_avg'] > 0:
        print(f"   Economia vs Media: {res['savings_vs_avg_formatted']} (Media: {res['average_price_formatted']})")

    print(f"\nTOP OFERTAS:")
    print(f"{'-'*75}")
    for idx, o in enumerate(res['offers'][:7], start=1):
        print(f"[{idx}] {o.price_formatted:>12} | {o.store:<16} | {o.title[:38]}")
        print(f"    Link: {o.link}")
    print(f"{'-'*75}\n")

if __name__ == '__main__':
    main()

