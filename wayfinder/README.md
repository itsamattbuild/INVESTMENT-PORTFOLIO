# Wayfinder — konwencja lokalnego trackera

Nie skonfigurowano żadnego issue trackera, więc mapa i tickety żyją jako pliki markdown w tym katalogu.

## Układ

```
wayfinder/
├── map.md              ← mapa (labels: wayfinder:map). Jedyny kanoniczny artefakt.
├── frontend-design.md  ← skill dostarczony przez użytkownika, używany przez ticket 0004
└── tickets/
    └── NNNN-slug.md    ← tickety, dzieci mapy
```

## Frontmatter ticketu

```yaml
id: 0003
title: ...
labels: [wayfinder:research | wayfinder:prototype | wayfinder:grilling | wayfinder:task]
parent: ../map.md
status: open | closed
assignee: null | <kto pracuje>
blocked_by: [0001, 0002]
```

## Operacje

- **Frontier** — tickety z `status: open`, pustym `assignee` i wszystkimi `blocked_by` zamkniętymi.
- **Claim** — wpisz siebie w `assignee` **przed** rozpoczęciem pracy. To odróżnia ticket zajęty od wolnego.
- **Rozwiązanie** — dopisz sekcję `## Resolution` na końcu ticketu, ustaw `status: closed`, dodaj wiersz do `## Decisions so far` w `map.md` z linkiem do ticketu.
- **Poza zakresem** — zamknij ticket i dopisz wiersz do `## Out of scope` w mapie. Nie trafia do `Decisions so far` — tam zapisujemy przebytą trasę, a granica zakresu nie jest jej etapem.

## Zasada

Jedna sesja = jeden ticket. Wyjątek: tickety badawcze (`wayfinder:research`) mogą lecieć równolegle.
