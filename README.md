# Redshift_Control
Redshift Control GTK panel
Poniżej znajduje się gotowy skrypt w Pythonie, który tworzy proste okno GTK z suwakami do temperatury i jasności oraz polami do wpisania geolokalizacji. Na tej podstawie Redshift ustala porę dnia i płynnie zmienia ustawienia wyświetlania.

### Co robi ten skrypt?

Skrypt nie zastępuje Redshifta, ale działa jako graficzny interfejs (frontend) do niego. Gdy przesuwasz suwaki lub wpisujesz dane i klikasz przycisk, skrypt w tle wywołuje odpowiednie komendy `redshift` z odpowiednimi parametrami.

---

### Krok 1: Wymagania

Zanim uruchomisz skrypt, upewnij się, że masz zainstalowane niezbędne pakiety. W Linux Mint (i innych dystrybucjach opartych na Debianie/Ubuntu) możesz je zainstalować poleceniem w terminalu:

```bash
sudo apt update
sudo apt install redshift python3-gi gir1.2-gtk-3.0
```

*   `redshift`: Podstawowy program, który będziemy kontrolować.
*   `python3-gi`: Biblioteka Pythona (PyGObject) pozwalająca na tworzenie aplikacji GTK.
*   `gir1.2-gtk-3.0`: Definicje introspekcji dla GTK3, potrzebne dla `python3-gi`.



Po uruchomieniu pojawi się okno z suwakami i polami, o które prosiłeś.

### Jak to działa?

*   **Ustawienia Geolokalizacji**: Wpisz swoją szerokość i długość geograficzną (możesz je znaleźć np. w Mapach Google, klikając prawym przyciskiem na swoją lokalizację). Po kliknięciu przycisku **"Ustaw lokalizację i uruchom tryb auto"**, skrypt wywoła `redshift -l LAT:LON`, co włączy automatyczne dostosowywanie barwy do pory dnia.
*   **Kontrola Ręczna**:
    *   **Suwak Temperatury**: Ustawia temperaturę barwową w Kelwinach. Niższe wartości (np. 3700K) dają cieplejszy, czerwonawy obraz. Wyższe wartości (np. 6500K) są neutralne (światło dzienne).
    *   **Suwak Jasności**: Reguluje ogólną jasność ekranu (w zakresie od 0.1 do 1.0). **Uwaga:** To nie jest to samo co podświetlenie matrycy, a raczej programowe przyciemnienie obrazu.
    *   Przycisk **"Zastosuj ustawienia ręczne"** wywołuje komendę `redshift -O TEMP -b BRIGHT`, gdzie `TEMP` i `BRIGHT` to wartości z suwaków. Jest to tryb jednorazowy, który wyłącza automatyczne dostosowywanie.
*   **Resetuj (wyłącz efekt)**: Ten przycisk wywołuje `redshift -x`, co natychmiastowo przywraca domyślne kolory i jasność monitora.

Mam nadzieję, że ten skrypt spełni Twoje oczekiwania i ułatwi Ci korzystanie z Redshifta
