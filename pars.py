import csv
import time
import requests
from bs4 import BeautifulSoup

def parse_5element_with_characteristics():
    catalog_url = "https://5element.by/catalog/571-buterbrodnicy"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    print("Шаг 1: Загрузка списка товаров из каталога...")
    try:
        response = requests.get(catalog_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при запросе к каталогу: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    items = soup.select(".product-card") or soup.select("[data-product]") or soup.select(".catalog-grid__item")
    
    product_links = []
    for item in items:
        link_elem = item.select_one("a[href]")
        if link_elem and link_elem.get("href"):
            href = link_elem["href"]
            full_link = "https://5element.by" + href if href.startswith("/") else href
            if full_link not in product_links:
                product_links.append(full_link)

    print(f"Найдено товаров в каталоге: {len(product_links)}. Начинаем сбор подробных характеристик со страниц товаров...")

    all_products_data = []

    for index, link in enumerate(product_links, 1):
        print(f"[{index}/{len(product_links)}] Парсим характеристики товара: {link}")
        try:
            prod_resp = requests.get(link, headers=headers, timeout=15)
            if prod_resp.status_code != 200:
                print(f"  -> Ошибка загрузки страницы товара (Статус: {prod_resp.status_code})")
                continue
            
            prod_soup = BeautifulSoup(prod_resp.text, "html.parser")

            title_elem = prod_soup.select_one("h1") or prod_soup.select_one(".product-title")
            title = title_elem.get_text(strip=True) if title_elem else "—"

            price_elem = prod_soup.select_one(".product-price__current") or prod_soup.select_one(".price") or prod_soup.select_one("[data-price]")
            price = price_elem.get_text(strip=True) if price_elem else "—"

            old_price_elem = prod_soup.select_one(".product-price__old") or prod_soup.select_one(".price-old")
            old_price = old_price_elem.get_text(strip=True) if old_price_elem else "—"

            status_elem = prod_soup.select_one(".product-status") or prod_soup.select_one(".status")
            status = status_elem.get_text(strip=True) if status_elem else "В наличии"

            specs = {}
            spec_rows = prod_soup.select(".specifications__item, .product-characteristics tr, .characteristics-table tr, .chars-item, table tr")
            
            for row in spec_rows:
                name_elem = row.select_one(".specifications__name, .chars-name, th, td:first-child")
                val_elem = row.select_one(".specifications__value, .chars-value, td:last-child")
                
                if name_elem and val_elem and name_elem != val_elem:
                    key = name_elem.get_text(strip=True)
                    val = val_elem.get_text(strip=True)
                    if key and val:
                        specs[key] = val

            if not specs:
                for div in prod_soup.select("[class*='spec'], [class*='char']"):
                    text = div.get_text(strip=True)
                    if ":" in text:
                        parts = text.split(":", 1)
                        if len(parts) == 2:
                            specs[parts[0].strip()] = parts[1].strip()

            power = specs.get("Мощность", specs.get("Мощность, Вт", "—"))
            panels = specs.get("Сменные панели", specs.get("Комплектация", specs.get("Насадки", "—")))
            coating = specs.get("Антипригарное покрытие", "—")
            
            all_specs_str = " | ".join([f"{k}: {v}" for k, v in specs.items()]) if specs else "Характеристики не найдены"

            all_products_data.append({
                "Наименование": title,
                "Цена (BYN)": price,
                "Старая цена (BYN)": old_price,
                "Статус": status,
                "Мощность": power,
                "Сменные панели / Насадки": panels,
                "Антипригарное покрытие": coating,
                "Полные характеристики": all_specs_str,
                "Ссылка": link + "#characteristics"
            })

            time.sleep(1.2)

        except Exception as e:
            print(f"  -> Ошибка при обработке товара: {e}")

    filename = "buterbrodnicy_full_comparison.csv"
    fieldnames = [
        "Наименование", "Цена (BYN)", "Старая цена (BYN)", "Статус", 
        "Мощность", "Сменные панели / Насадки", "Антипригарное покрытие", 
        "Полные характеристики", "Ссылка"
    ]

    with open(filename, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        if all_products_data:
            writer.writerows(all_products_data)

    print(f"\n Успешно! Собрано товаров: {len(all_products_data)}. Файл сохранен как '{filename}'.")

if __name__ == "__main__":
    parse_5element_with_characteristics()