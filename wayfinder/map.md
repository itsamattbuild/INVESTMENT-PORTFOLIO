---
labels: [wayfinder:map]
title: Lokalny tracker portfela akcji US
---

# Lokalny tracker portfela akcji US

## Destination

Kompletny spec v1 lokalnej aplikacji portfelowej — na tyle rozstrzygnięty, że kolejne sesje mogą ją zbudować bez podejmowania decyzji projektowych.

Spec musi zawierać: wybrane źródło cen, model danych zapisywanych na dysku, algorytm rebalansu do wag docelowych, sposób liczenia P/L, kierunek wizualny i układ ekranów, oraz sposób uruchamiania aplikacji.

Mapa jest zamknięta, gdy nie zostało nic do **zdecydowania** — tylko do zbudowania.

## Notes

**Domena.** Prywatny tracker portfela dla jednej osoby, działający wyłącznie lokalnie. Prywatność jest powodem istnienia projektu — żadne dane portfela nie opuszczają dysku.

**Ustalona architektura (runda 1–4 grillowania):**

- Python + FastAPI serwujące na `localhost`, front to HTML + CSS + minimum JS, szablony Jinja.
- Dane trzymane lokalnie na dysku, zarządzane przez Pythona.
- Zakres v1: **wyłącznie akcje amerykańskie w USD**. Jedna waluta, jedna klasa aktywów.
- Model **transakcyjny**: zapisujemy transakcje (kupno/sprzedaż/split), pozycje i średnią cenę liczymy z nich.
- **Brak gotówki** jako trwałego bytu. Tryb dokupowania przyjmuje doraźne pole „kwota do zainwestowania”.
- **Wagi docelowe trwałe**, definiowane per spółka, wszystkie edytowalne z jednego miejsca. Apka przy starcie pokazuje odchylenie od celu.
- **Akcje ułamkowe** dozwolone, zaokrąglanie do 4 miejsc po przecinku.
- Rebalans w dwóch trybach: domyślnie **tylko dokupowanie**, opcjonalnie pełny (z sprzedażą). Powód: sprzedaż w USA generuje zdarzenie podatkowe.
- **Split** jako ręcznie wprowadzane zdarzenie w modelu danych od pierwszego dnia.
- **P/L rozbite** na zrealizowany i niezrealizowany, nigdy zsumowane w jedną liczbę.
- **Prowizja** jako opcjonalne pole przy transakcji, domyślnie 0.
- Ceny mają **timestamp pobrania** widoczny w UI. Brak sieci → ostatnie znane ceny z datą, nigdy pusty ekran.

**Skille do wywołania w każdej sesji:** `grilling` i `domain-modeling`. Tickety prototypowe dodatkowo `prototype`.

**Design.** Użytkownik dostarczył skill `frontend-design` (zapisany w `wayfinder/frontend-design.md`) — stosować, ale z ograniczeniem: **to jest narzędzie, nie strona marketingowa**. Charakter wydajemy na typografię i paletę; układ danych zostaje konwencjonalny i gęsty; zero animacji poza feedbackiem na akcję. Katalogi inspiracji (Mobbin, Refero, SaaSFrame) odrzucone — płatne i skonwergowane do jednego wyglądu.

**Preferencja użytkownika:** uczy się Pythona. Przy równorzędnych opcjach wybierać tę, w której więcej dzieje się po stronie Pythona, a mniej w toolingu frontendowym.

## Decisions so far

<!-- pusto: kartowanie niczego nie rozstrzyga -->

## Not yet specified

- **Historia wartości portfela w czasie (equity curve).** Wymaga albo codziennych snapshotów przy nieregularnym otwieraniu apki, albo pobierania pełnej historii cen i odtwarzania. Wraca, gdy model danych stoi.
- **Dywidendy.** Osobny typ zdarzenia, osobne źródło danych, 15% podatek u źródła z US. Wraca po ustaleniu modelu transakcji.
- **Automatyczne wykrywanie splitów** z danych giełdowych zamiast ręcznego wprowadzania. Zależy od tego, co potrafi wybrane źródło cen.
- **Obligacje skarbowe i wielowalutowość.** Wciągnęłoby do modelu PLN, kurs NBP i wycenę narastającą w czasie. Świadomie odłożone, nie odrzucone — wraca, gdy część akcyjna działa.
- **Backup i migracja formatu danych.** Co się dzieje, gdy schemat się zmieni, a na dysku leżą stare pliki.
- **Walidacja i obsługa błędów przy wprowadzaniu transakcji.** Zależy od modelu danych.
- **Sposób dystrybucji.** Czy apka ma się dać odpalić bez terminala. Zależy od ticketu o cyklu życia aplikacji.

## Out of scope

- **Lokalny LLM zarządzający aplikacją.** Ma sens dopiero, gdy istnieje stabilne API do portfela, po którym może chodzić. Projektowany teraz wykrzywiłby architekturę pod nieokreślone jeszcze wymagania. Wraca jako osobna mapa.
- **Import pliku z XTB.** Użytkownik świadomie deleguje to przyszłemu lokalnemu modelowi — nie chce wysyłać wyciągu do modelu w chmurze. Wychodzi razem z LLM-em.
- **Instrumenty inne niż akcje amerykańskie w USD.** Granica v1.

## Tickety

Otwarte tickety leżą w `wayfinder/tickets/`. Frontier = otwarte, odblokowane, nieprzypisane.

| # | Ticket | Typ | Status | Blokowany przez |
|---|--------|-----|--------|-----------------|
| 0001 | [Źródło cen dla akcji amerykańskich](tickets/0001-zrodlo-cen.md) | research | open | — |
| 0002 | [Model danych i format zapisu na dysku](tickets/0002-model-danych.md) | grilling | open | 0001 |
| 0003 | [Algorytm rebalansu do wag docelowych](tickets/0003-algorytm-rebalansu.md) | grilling | open | — |
| 0004 | [Kierunek wizualny i układ głównego ekranu](tickets/0004-kierunek-wizualny.md) | prototype | open | — |
| 0005 | [Cykl życia aplikacji i uruchamianie](tickets/0005-cykl-zycia.md) | grilling | open | 0001 |
