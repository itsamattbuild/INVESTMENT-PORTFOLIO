---
id: 0004
title: Kierunek wizualny i układ głównego ekranu
labels: [wayfinder:prototype]
parent: ../map.md
status: open
assignee: null
blocked_by: []
---

# Kierunek wizualny i układ głównego ekranu

## Question

Jak ta aplikacja wygląda i z jakich ekranów się składa?

Do rozstrzygnięcia:

1. **Jakie ekrany w ogóle istnieją.** Kandydaci: przegląd portfela, wprowadzanie transakcji, ustawianie wag docelowych, wynik rebalansu, historia transakcji. Czy to osobne strony, czy jedna gęsta strona z sekcjami?
2. **Co jest na ekranie głównym i w jakiej kolejności.** To ekran, na który patrzysz codziennie — musi w pierwszej sekundzie odpowiadać na pytanie, po które go otwierasz. Ustalić, jakie to pytanie.
3. **Kierunek wizualny.** Paleta, typografia, gęstość. Stosować skill `frontend-design`, ale z ograniczeniem z Notes mapy: to narzędzie, nie strona marketingowa.
4. **Jak pokazujemy odchylenie od wagi docelowej.** Liczba, pasek, kolor? To centralny element całej aplikacji.
5. **Jak pokazujemy nieaktualne ceny.** Timestamp musi być widoczny, ale nie może dominować. Jak wygląda stan „dane sprzed 3 dni, brak sieci".
6. **Kolor przy zysku i stracie.** Zielony/czerwony to konwencja, ale przy daltonizmie i przy dużej gęstości danych bywa nieczytelna. Rozstrzygnąć świadomie.

## Kontekst

Ustalenia z grillowania, przyjęte jako dane:

- HTML + CSS + minimum JS, szablony Jinja serwowane przez FastAPI. Bez build-stepu frontendowego.
- Skill `frontend-design` dostarczony przez użytkownika leży w `wayfinder/frontend-design.md`.
- Katalogi inspiracji odrzucone: płatne i skonwergowane do jednego wyglądu. Kierunek wypracowujemy, nie kopiujemy.
- Wolne źródła podglądu, jeśli potrzebne: strony marketingowe Snowball Analytics, Getquin, Sharesight, Kubera, Portseido.
- **Wszystkie teksty w interfejsie po angielsku.** Jeden język w całym stosie — etykieta na ekranie ma się nazywać tak samo jak pole w kodzie.

## Wynik

Statyczny prototyp HTML z atrapowymi danymi, podlinkowany z tego ticketu. Prototyp jest do wyrzucenia — służy do tego, żeby użytkownik zobaczył i zareagował, nie do tego, żeby stał się kodem produkcyjnym.
