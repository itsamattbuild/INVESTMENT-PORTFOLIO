---
id: 0001
title: Źródło cen dla akcji amerykańskich
labels: [wayfinder:research]
parent: ../map.md
status: open
assignee: null
blocked_by: []
---

# Źródło cen dla akcji amerykańskich

## Question

Skąd aplikacja pobiera aktualne ceny akcji amerykańskich i jak zachowuje się, gdy źródło zawiedzie?

Do rozstrzygnięcia:

1. **Które źródło.** Kandydaci: `yfinance` (darmowe, nieoficjalne, historycznie się psuje przy zmianach po stronie Yahoo), Stooq (CSV, stabilne, jakość danych US do sprawdzenia), Alpha Vantage / Finnhub (oficjalne API, darmowy tier z limitami — sprawdzić jakimi), Tiingo. Zbadać: czy biblioteka jest utrzymywana, jak często się psuje, jakie limity zapytań, czy wymaga klucza API.
2. **Fallback.** Czy warto mieć drugie źródło i jak wygląda przełączenie.
3. **Kształt odpowiedzi.** Co dokładnie zwraca źródło dla jednego tickera: ostatnia cena, cena zamknięcia, timestamp, waluta. To determinuje kształt cache'u cen w modelu danych (ticket 0002).
4. **Walidacja tickera.** Jak aplikacja sprawdza, że wpisany ticker istnieje, zanim użytkownik zapisze transakcję.
5. **Splity i korekty.** Czy źródło udostępnia informację o splitach — wpływa na to, czy `Automatyczne wykrywanie splitów` może kiedyś wyjść z mgły.
6. **Zachowanie przy błędzie.** Ustalone już: pokazujemy ostatnie znane ceny z timestampem. Ticket ma określić, jakie błędy realnie występują (rate limit, brak sieci, ticker zniknął, źródło zwraca śmieci) i jak je rozróżnić.

## Kontekst

Ustalenia z grillowania, które ten ticket przyjmuje jako dane:

- Wyłącznie akcje amerykańskie, wyłącznie USD. Bez GPW, bez ETF-ów zagranicznych, bez walut.
- Ceny pobierane przy starcie aplikacji.
- Każda cena musi nieść czas pobrania.
- Preferencja: rozwiązanie w czystym Pythonie, bez zewnętrznych usług płatnych.

## Wynik

Plik markdown w repo z porównaniem źródeł, rekomendacją i działającym przykładem kodu pobierającego cenę dla kilku tickerów. Rekomendacja musi być uzasadniona ryzykiem awarii, nie wygodą API.
