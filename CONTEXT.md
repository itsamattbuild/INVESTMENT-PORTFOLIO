# Context

Słownik pojęć tej aplikacji. Wyłącznie terminy domenowe — żadnych decyzji implementacyjnych.

## Transakcja

Zdarzenie, które zaszło na rachunku maklerskim. Fakt, nie stan. Trzy rodzaje: **kupno**, **sprzedaż**, **split**.

Transakcje są jedynym źródłem prawdy o portfelu. Wszystko inne jest z nich wyliczane.

## Pozycja

Wynik zsumowania wszystkich transakcji dla jednej spółki: liczba posiadanych sztuk i średni koszt nabycia. Pozycja nie jest zapisywana — jest liczona przy każdym otwarciu aplikacji.

Odróżniaj od transakcji: pozycja to *stan*, transakcja to *zdarzenie*.

## Split

Podział akcji — zmiana liczby posiadanych sztuk bez przepływu pieniędzy. Wprowadzany ręcznie jako osobny rodzaj transakcji.

Nie mylić z kupnem: split nie zmienia wartości pozycji ani łącznego kosztu nabycia, tylko liczbę sztuk i cenę jednostkową.

## Waga aktualna

Udział pozycji w wartości całego portfela, liczony po **aktualnych cenach rynkowych**. Mianownikiem jest suma wycen wszystkich pozycji — gotówka nie wchodzi do modelu.

## Waga docelowa

Udział, jaki dana spółka *ma mieć* w portfelu. Trwała, zapisywana, definiowana osobno dla każdej spółki. Wyraża politykę portfela, nie jego stan.

## Odchylenie

Różnica między wagą aktualną a docelową. To jest liczba, po którą otwierasz aplikację.

## Kwota do zainwestowania

Pieniądze, które zamierzasz wpłacić — podawane doraźnie przy uruchamianiu rebalansu, nigdzie nie zapisywane.

Świadomie **nie** jest to „saldo gotówki": aplikacja nie śledzi gotówki na rachunku, bo w praktyce jej tam nie ma.

## Rebalans

Wyliczenie, co kupić (i opcjonalnie co sprzedać), żeby wagi aktualne zbliżyły się do docelowych. Dwa tryby:

- **dokupowanie** — domyślny, rozdziela *kwotę do zainwestowania*, nic nie sprzedaje;
- **pełny** — dopuszcza sprzedaż, świadomie włączany, bo sprzedaż generuje zdarzenie podatkowe.

## Zysk niezrealizowany

Różnica między aktualną wyceną otwartych pozycji a ich kosztem nabycia. Zmienia się z każdą ceną.

## Zysk zrealizowany

Zysk lub strata domknięta sprzedażą. Nie zmienia się już nigdy.

Nigdy nie sumowany z niezrealizowanym w jedną liczbę — powstałaby wartość, której nie da się zinterpretować.

## Snapshot ceny

Cena spółki wraz z **czasem jej pobrania**. Aplikacja nie zna pojęcia „cena" bez timestampu: bez niego nie odróżnisz spadku portfela od awarii pobierania.
