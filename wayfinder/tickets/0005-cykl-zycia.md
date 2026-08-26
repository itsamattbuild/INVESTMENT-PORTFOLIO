---
id: 0005
title: Cykl życia aplikacji i uruchamianie
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: [0001]
---

# Cykl życia aplikacji i uruchamianie

## Question

Co się dzieje od momentu, gdy chcesz otworzyć aplikację, do momentu, gdy patrzysz na aktualne dane?

Do rozstrzygnięcia:

1. **Jak się to odpala.** Komenda w terminalu? Skrypt `.command` do dwukliku? Czy serwer ma chodzić w tle stale, czy startować na żądanie?
2. **Co robi start.** Kolejność: wczytaj dane → pobierz ceny → przelicz → pokaż. Czy pobieranie cen blokuje wyświetlenie strony, czy strona pokazuje się od razu ze starymi cenami i odświeża się po pobraniu?
3. **Ile trwa pobranie.** Przy kilkunastu tickerach — sekwencyjnie czy równolegle? Czy potrzebny jest wskaźnik postępu.
4. **Odświeżanie w trakcie.** Czy jest przycisk „pobierz ceny teraz", czy tylko przy starcie.
5. **Zamykanie.** Co ubija serwer. Co się dzieje z niezapisanymi danymi.
6. **Jeden użytkownik, jedna instancja.** Co, gdy odpalisz apkę dwa razy — port zajęty, dwa procesy piszące do tego samego pliku.
7. **Gdzie lądują logi i błędy.** Gdy pobranie cen padnie, musisz mieć gdzie zajrzeć.

## Kontekst

Ustalenia z grillowania, przyjęte jako dane:

- FastAPI serwujące na `localhost`.
- Ceny pobierane przy starcie aplikacji.
- Brak sieci → ostatnie znane ceny z timestampem, nigdy pusty ekran.
- Użytkownik uczy się Pythona — preferować rozwiązania, które są czytelne w Pythonie, nad sprytne.

## Wynik

Opisany cykl życia aplikacji od uruchomienia do zamknięcia, z jawnym zachowaniem dla każdego trybu awarii.
