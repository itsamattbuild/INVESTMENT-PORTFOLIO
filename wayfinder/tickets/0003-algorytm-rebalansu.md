---
id: 0003
title: Algorytm rebalansu do wag docelowych
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: []
---

# Algorytm rebalansu do wag docelowych

## Question

Jak dokładnie aplikacja liczy, co sprzedać i co dokupić, żeby osiągnąć wagi docelowe?

Do rozstrzygnięcia:

1. **Tryb dokupowania.** Użytkownik podaje kwotę do zainwestowania. Algorytm rozdziela ją tak, żeby maksymalnie zbliżyć się do wag docelowych. Pytanie: co znaczy „maksymalnie zbliżyć" — minimalizacja sumy odchyleń? maksymalnego odchylenia? Te dwie definicje dają różne odpowiedzi.
2. **Cele nieosiągalne bez sprzedaży.** Spółka ma 25% przy celu 15%. W trybie tylko-dokupowania nie da się jej zmniejszyć inaczej niż rozcieńczając resztą. Co, gdy kwota jest za mała, żeby to naprawić? Algorytm musi to powiedzieć wprost, nie po cichu zwrócić bezsensowny wynik.
3. **Tryb pełny.** Z dozwoloną sprzedażą. Czy liczy dokładne trafienie w cele, czy zostawia margines?
4. **Próg minimalnej transakcji.** Czy sugerować dokupienie za 3 USD. Prawdopodobnie potrzebny próg odcięcia.
5. **Wagi, które nie sumują się do 100%.** Co robi aplikacja, gdy suma celów wynosi 90% albo 110%. Walidacja twarda czy normalizacja?
6. **Spółki spoza celów.** Masz pozycję, dla której nie ustawiłeś wagi docelowej. Traktujemy ją jako cel 0% (do sprzedaży) czy jako nietykalną?
7. **Prezentacja wyniku.** Lista „kup 2.3741 NVDA za 431 USD" — czy pokazujemy też wagę przed i po, i przewidywane odchylenie resztkowe?

## Kontekst

Ustalenia z grillowania, przyjęte jako dane:

- Wagi docelowe trwałe, definiowane per spółka, wszystkie edytowalne z jednego miejsca.
- Domyślny tryb: tylko dokupowanie. Pełny rebalans z sprzedażą świadomie włączany.
- Kwota do zainwestowania to doraźne pole, nigdzie nie zapisywane.
- Akcje ułamkowe, 4 miejsca po przecinku.
- Wagi liczone względem samych pozycji — bez gotówki w mianowniku.

## Wynik

Algorytm opisany na tyle precyzyjnie, że da się go zaimplementować bez dopytywania, plus zestaw scenariuszy brzegowych z oczekiwanymi wynikami — gotowa podstawa pod testy.
