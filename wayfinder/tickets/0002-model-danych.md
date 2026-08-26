---
id: 0002
title: Model danych i format zapisu na dysku
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: [0001]
---

# Model danych i format zapisu na dysku

## Question

Jak dokładnie wygląda to, co leży na dysku, i jaki jest schemat każdego bytu?

Do rozstrzygnięcia:

1. **Format zapisu.** SQLite czy pliki JSON? SQLite daje zapytania, transakcyjność i odporność na przerwany zapis; JSON jest czytelny gołym okiem, edytowalny ręcznie i wersjonowalny gitem. To decyzja trudno odwracalna.
2. **Schemat transakcji.** Pola: ticker, typ (kupno / sprzedaż / split), liczba sztuk, cena, data, prowizja, notatka. Co jest wymagane, co opcjonalne, jakie typy liczbowe (`Decimal` czy `float` — przy pieniądzach to nie jest kosmetyka).
3. **Schemat zdarzenia split.** Jak reprezentujemy split 10:1 tak, żeby przeliczenie pozycji i średniej ceny wychodziło poprawnie i było odwracalne przy pomyłce.
4. **Schemat wag docelowych.** Trwałe, per spółka. Gdzie leżą — obok transakcji czy osobno? Co się dzieje z wagą spółki, którą sprzedałeś do zera?
5. **Cache cen.** Kształt zależy od wyniku ticketu 0001. Co przechowujemy, jak długo, czy trzymamy historię cen czy tylko ostatnią.
6. **Gdzie fizycznie leżą pliki.** Katalog aplikacji, `~/Library/Application Support`, czy konfigurowalna ścieżka.
7. **Jak liczymy pozycję z transakcji.** Średnia ważona kosztu, kolejność zdarzeń, obsługa sprzedaży (jaka metoda kosztu — średnia czy FIFO; to wpływa na zrealizowany P/L i na rozliczenie podatkowe).

## Kontekst

Ustalenia z grillowania, przyjęte jako dane:

- Model transakcyjny, nie pozycyjny. Transakcje to fakty, pozycje to wynik.
- Brak gotówki jako trwałego bytu.
- Akcje ułamkowe, zaokrąglanie do 4 miejsc.
- P/L rozbite na zrealizowany i niezrealizowany.
- Split jako ręczne zdarzenie, obecne w modelu od pierwszego dnia.
- Prowizja opcjonalna, domyślnie 0.

## Wynik

Schemat każdego bytu wraz z uzasadnieniem wyboru formatu. Zaktualizowany `CONTEXT.md` o terminy, które się przy okazji doprecyzują.
