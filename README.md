# PROJEKT WDP - Aplikacja do zarzadzania nauką

Aby uruchomić aplikację należy pobrać wymagane biblioteki `pip install requirements.txt`

Pliki do uruchomienia:
- `main.py` - pełna wersja aplikacji [GUI]
- `cli.py` - prosta wersja konsolowa

Ten program pomoże Ci rozłożyć naukę w czasie, abyś zdążył na każdy egzamin bez stresu.

***--- INSTRUKCJA ---***

1. *OKNO POWITALNE*

Na ekranie początkowym znajduje się szybki podgląd (licznik do następnego egzaminu oraz pasek postępu aktualizujący się na bieżąco). Znajdziesz tu przycisk uruchamiający główne okno, tę instrukcję, wybór języka oraz przycisk wyjścia.
Uwaga: Jeśli zmienisz język, musisz uruchomić aplikację ponownie.

2. *GŁÓWNE OKNO*


To centrum dowodzenia z planem nauki. Z tego miejsca możesz:
- Dodawać i edytować egzaminy
- Przeglądać i generować plan
- Zmieniać statusy zadań
- Przeglądać i czyścić bazę danych

**Ważne:** Jeśli dodasz egzaminy z zadaniami, musisz kliknąć "Generuj Plan". Inaczej zadania nie będą miały przypisanych dat.

Kolory wpisów:
- Biały: Zadanie do wykonania
- Zielony: Zadanie wykonane *(nie zmieni daty przy ponownym generowaniu)*
- Szary: Zadanie zaległe *(termin minął)*
- Czerwony: Dzień egzaminu

3. *DODAWANIE EGZAMINU*

- Kliknij przycisk „Dodaj Egzamin”
- Wpisz przedmiot i formę *(np. Kolokwium)*
- Wybierz datę *(możesz użyć kalendarza, aby ją zaznaczyć)*
- Wpisz tematy/zadania *(jeden pod drugim)*
- Kliknij „Zapisz”
*(Pamiętaj, aby potem wygenerować plan!)*

4. PRZEGLĄDANIE BAZY DANYCH

Po kliknięciu w „Wszystkie Egzaminy” zobaczysz listę wszystkich wpisów (aktywnych i archiwalnych). Możesz tu:
- Usunąć zaznaczony egzamin
- Usunąć wszystkie archiwalne egzaminy *(aktywne zostaną nienaruszone)*
- Zobaczyć szczegóły każdego z egzaminów

W widoku szczegółowym możesz zmieniać statusy zadań oraz edytować egzamin lub konkretne zadania.

5. EDYCJA I BLOKADA PLANOWANIA

Z poziomu edycji możesz zmieniać nazwy, daty oraz dodawać/usuwać tematy.

**Blokada planowania:**
Jest przydatna przy manualnej zmianie daty dla zadania. Opcja ta włącza się automatycznie po ręcznej zmianie daty (można ją też włączyć ręcznie).

*Przykład użycia:*
Chcesz przełożyć zadania na inne dni niż proponuje algorytm (np. przez wyjazd). Dzięki blokadzie, gdy ponownie wygenerujesz plan (np. dodając nowe tematy), algorytm poukłada wszystko inne, ale zablokowanego wpisu nie ruszy. Zostanie dokładnie tam, gdzie chciałeś.

## Zródła:
- Materiały pomocnicze wyraźnie podlinkowane poniżej przy każdym pliku
- Google Gemini 3 Pro [data dostępu: 23.01.2026]
  - Poniżej przy każdym pliku dodalem informacje jak powstawał kod i jest tam wspomniane z czym pomoglo AI, co zrobilo w całości a co jest wykonene samodzielnie.
  - Też często AI pomagało mi w zrozumieniu pewnych zagadnień np. jak używać klas lub dawało przykłady jak np. jak wstawiać elementy tkinter, ale nie robiło tego za mnie.
- Do dużej części kodu stosowałem umiejętności pozyskane w liceum, bez dodatkowych źródeł (często metodą prób i błędów, aż nie zwróci oczekiwanego wyniku) w ten sposób powstał np. algorytm rozkładania tematów na daty w `planner.py`
- Przy artykułach tam gdzie znalazłem autora to go wpisałem, ale na stronie docs.python.org nie ma takich informacji, a wiekszosc informacji czerpałem z tamtąd

## Wstępne informacje:
- folder `_dev_tools` ***nie jest częścią projektu*** (zawiera własne README), a powstał, bo to testowania aplikacji zacząłem z niej korzystać i aby nie musieć cały czas jej uruchamiać przez IDE to postanowiłem wyeksportować ją do pliku wykonywalnego.
- pliki językowe w folderze `languages` działają na zasadzie map (słowników) i powstały z pomocą AI a dokladniej poprosiłem Google Gemini aby zebrał z kodu wszystkie frazy i stworzył słownik. Potem mi zostało podmienienie fraz w kodzie na odpowiedniki w tym słowniku, a to pozwoliło na dodanie różnych wersji językowych aplikacji. Tłumaczenie również zrobiło AI.
- `cli.py` to pierwotna wersja, ktorej uzywalem do testowania algorytmu planującego. Zródła:
  - uuid - https://docs.python.org/3/library/uuid.html [13.12.2025]
- Projekt zaczął powstawać 10.12.2025. Cała historia jest na gitlabie.

## Opis projektu z podziałem na pliki:

### `main.py` - *główny plik programu*

1. **Materialy pomocnicze:**
- tkinter https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]
- tkinter.ttk https://docs.python.org/3/library/tkinter.ttk.html [16.01.2026]

2. **Opis kodu:**
- `__init__` - funkcja wykonujaca sie raz na początku. Ładuje dane z bazy danych, ustawia pola tkintera (labele, przyciski, ramki, combobox jezyka(funkcja `setup_language_selector`)), wczytuje odpowiednią mape językow zczytana z pola settings w bazie danych, ustawia styl przyciskow wykorzystywany w reszcie programu (btn_style), uruchamia pierwsze odswiezenie danych na ekranie powitalnym (`refresh_dashboard`)
- `refresh_dashboard` - funkcja odswiezajaca dane w labelach ustawionych przez `__init__` za pomoca label.config. W kodzie sa komentarze dla roznych sekcji tej funkcji(np A - obliczenie i ustawienie postepu ogolnego, B - obliczenie i ustawienie postepu dziennego). Funkcja ta jest uruchamiana raz na poczatku a potem przez callback otrzymany od dalszej czesci programu, aby dane w tym oknie byly zawsze aktualne.
- `setup_language_selector` - funkcja uruchamiana przez `__init__` sluzy dodaniu do okna programu comboboxa z lista jezykow do wyboru, a takze wykrywa zmiane wyboru wprowadzona przez uzytkownika i zmienia jezyk w bazie danych aby po ponownym uruchomieniu programu wystartowac z wybranym jezykiem.
- `open_manual` - uruchamia klase `ManualWindow`(z pliku `manual.py`) przekazujac jej zmienna zawierajaca slownik jezykowy i styl przyciskow
- `open_plan_window` - uruchamia klase `PlanWindow`(z pliku `plan.py`) przekazujac jej slownik jezykowy, styl przyciskow, wczesniej wczytane dane z bazy oraz callback do odswiezania okna powitalnego.

3. **Sposób pisania**

W pewnym momencie pisania mialem za duzo linijek (wszystkie funkcje programu byly w tym jednym pliku) i Google Gemini podpowiedzial mi aby podzielic to na klasy i oddzielne pliki oraz wytlumaczyl jak to poprawnie zrobic (nie zrobil tego za mnie). Funkcje `__init__` napisalem z pomoca stron z punktu 1. Funkcje `refresh_dashboard` napisalem sam pierwotnie jako kod w init ale AI podpowiedzialo aby to zamknac w funkcji i odswiezac po zmianach z pomoca callbacka oraz wytlumaczyl co to jest callback. Funkcje `setup_language_selector` napisalem sam z pomoca stron z punktu 1 aby okielznac comboboxa. Funkcje `open_manual` i `open_plan_window` zaproponowalo mi AI (nie wplywajac na zawartosc klas ManualWindow i PlanWindow) przy dzieleniu dlugiego kodu na klasy. Jak pisalem kod dalej i dalej to zauwazylem ze przy tworzeniu przyciskow caly czas powtarzam ten sam styl, wiec zapytalem AI czy da sie to jakos ubrac w zmienna i dodawac do kazdego przycisku tylko ja a nie caly kod. Dostalem przyklad jak to zrobic i samodzielnie zaimplementowalem.


### `plan.py` - *główne okienko z planem*

1. **Materiały pomocnicze:**
- tkinter - https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]
- ttk.Treeview https://docs.python.org/3/library/tkinter.ttk.html#ttk-treeview [16.01.2026]
- datetime https://docs.python.org/3/library/datetime.html [14.12.2025]

2. **Opis kodu:**
- `__init__` - ustawienie elementow w oknie oraz 1 wywolanie odswiezania tabeli
- `refresh_table` - funkcja uzupelniajaca tabele. Najpierw bierze zalegle tematy i wstawia je na gore a potem wstawia tematy z datami (plan na przyszlosc)
- `run_and_refresh` - funkcja uruchamiana przez przycisk generujacy plan. Uruchamia planowanie a po ukonczeniu automatycznie odswieza tabele. Jesli przy planowaniu wystapi blad to pokaze go jako komunikat
- `toggle_status` - funkcja zmieniajaca status zadania "todo" / "done"
- `clear_database` - funkcja usuwajaca wszystkie wpisy z bazy danych
- `open_add_window` - funkcja otwierajaca okno dodawania egzaminu
- `open_edit` - funkcja otwierajaca okno edycji
- `open_archive` - funkcja otwierajaca okno archiwum. Zawiera wrappery funkcji edycji, bo w archiwum mozna edytowac wiec trzeba dac mozliwosc otworzenia okien edycji z poziomu archiwum.

3. **Sposób pisania:**

Kod napisany samodzielnie, z pomoca artykulow z punktu 1. Dodatkowo AI pomoglo mi zrobic wrappery do funkcji `open_archive` oraz ze zrobieniem działających callbacków w funkcjach `open_add_window` i `open_edit` aby po zapisaniu zmian w tamtych oknach automatycznie odswiezyc tabele.

### `planner.py`

1. **Materiały pomocnicze:**
- datetime https://docs.python.org/3/library/datetime.html [14.12.2025]

2. **Opis kodu:**
- `date_format` - funkcja, ktora dostaje stringa lub obiekt date i zwraca zawsze obiekt date. Potrzebne do obliczen w dalszej czesci kodu
- `callendar_create` - funkcja tworzaca mape {data: egzamin} dla calego przedzialu od dzisiaj do ostatniego egzaminu
- `topics_list_create` - funkcja tworzaca tablice tematow dla kazdego egzaminu (rozroznialne po id). Funkcja dostaje baze danych i id egzaminu, dla tego id szuka tematow ktore nie za zablokowane i maja status "todo" a nastepnie wstawia je w tablice, ktora jest obslugiwana w dalszej czesci programu.
- `plan` - glowna funkcja planujaca. To ona wywoluje tworzenie kalendarza i potem dla kazdego egzaminu wywoluje funkcje tworzaca tablice z tematami. Dla kazdego egzaminu oblicza ile tematow dziennie trzeba wstawic aby wyrobic sie do daty egzaminu od dzisiaj. Ustala date od kiedy do kiedy (okienka pomiedzy egzaminami) a nastepnie wpisuje id tematow do mapy callendar. Na koniec dla kazdego id z callendar szuka odpowiednika w bazie danych i ustawia scheduled date na ta z callendar i baza jest zaktualizowana.

3. **Sposób pisania:**

Cały kod `planner.py` zostal napisany bez użycia AI a jedyna pomoc to material pomocniczy, ktory byl potrzebny do zrozumienia jak dziala format datetime. Cała logika tego planowania zostala opracowana przeze mnie samodzielnie. Na poczatku na kartce a potem w kodzie. W pliku jest tez funkcja `plan_old`, ktora byla napisana jako pierwsza ale zawiera male bledy logiczne, ktore w niepoprawny sposob przypisywaly daty do egzaminow. Zostawilem ja aby pokazac z czego powstala ta wlasciwa. Dzialaja na tej samej zasadzie ale druga jest napisana czysciej i czytelniej.

### `storage.py`

1. **Materiały pomocnicze:**
- pathlib https://docs.python.org/3/library/pathlib.html [13.12.2025]
- json https://docs.python.org/3/library/json.html [13.12.2025]
- platformdirs https://pypi.org/project/platformdirs/ [15.01.2026]


2. **Opis kodu:**

`storage.py` zawiera 3 główne funkcje:
- load - sluży do wczytywania bazy danych z pliku json dla dalszej części programu
- save - służy do zapisywania bazy danych operacji wykonanych przez program albo użytkownika
- load_language - wczytuje plik ze zmiennymi językowymi (zapisanymi w json jako słowniki)
   

3. **Sposób pisania:**
- funkcje `load`,`save`,`load_language` napisałem samodzielnie z pomocą materiałów pomocniczych jak działa pathlib i jak obslugiwać pliki json, linki do stron u góry. Dodatkowo użyłem Google Gemini podpowiedział mi aby w `save` ustawić `default=str` aby formaty się zgadzały i nie powodowały błedów oraz aby zabezpieczyć funkcje `load_languages` przed dostaniem nieistniejącego kodu języka.
- Początkowe fragmenty kodu wyroznione ponizej są napisane przez Google Gemini i służą rozpoznawaniu w jakim systemie uruchomiono program oraz ustalają ścieżke bazy danych. Zrobione jest to dla plików w `_dev_tools`(które nie są częścią projektu, a służą do eksportowania aplikacji do pliku wykonywalnego. Oznaczone `*`). Fragmenty z opisami poniżej:

`*`Przełącznik True / False | mówi programowi czy ma korzystać z bazy danych zapisanej w pliku projektu czy w folderach systemowych:
```
USE_SYSTEM_STORAGE = True
```
`*`Ustalenie gdzie znajduje się baza danych. Lokalna - projekt, systemowa - w katalogu systemowym
```
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.json"

APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"
SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.json"
```
`*`Wybór z której ściezki program ma korzystać na podstawie `USE_SYSTEM_STORAGE`
```
if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = SYSTEM_DB_PATH
else:
    DB_PATH = LOCAL_DB_PATH
```
Znalezienie gdzie znajdują się pliki z językami:
```
LANG_DIR = CORE_DIR.parent / "languages"
```

### `add_exam.py`

1. **Materiały pomocnicze:**
- tkinter - https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]
- tkcalendar - https://pypi.org/project/tkcalendar/ [14.01.2026] [autor: j_4321]
- uuid - https://docs.python.org/3/library/uuid.html [13.12.2025]
- datetime - https://docs.python.org/3/library/datetime.html [14.12.2025]

2. **Opis kodu:**
- `__init__` - Ustawia elementy tkinter takie jak labele i pola entry na ekranie. Obiekty entry umozliwiaja wprowadzenie danych o egzaminie przez uzytkownika. Tutaj tez uzywam modulu tkcalendar, aby zamiast wpisywac date mozna bylo otworzyc maly kalendarzyk i zaznaczyc.
- `save_new_exam` - funkcja zapisujaca nowy egzamin w bazie. Zbiera dane z pól entry oraz zamienia tekst z pola na tematy na tablice tematow. Potem dodaje wpis do bazy danych exams z danymi egzaminu oraz dla kazdego tematu z tablicy dodaje wpis to topics.

3. **Sposób pisania:**

Funkcjonalnosc tych funkcji napisalem wczesniej sam w pliku main, ale Google Gemini pomogl mi ten kod przeniesc do osobnego pliku jako klase. Przy tej operacji glowny kod z wyjatkiem nazw zmiennych sie nie zmienil.

Dodatkowo mialem problem przy dodawaniu tkcalendar, dokumentacja nie pomogla mi wystarczajaco i to tez AI wytlumaczylo jak to poprawnie zaimplementowac. Dotyczy to tylko tego fragmentu kodu:
```
self.entry_date = DateEntry(self.win, width=27, date_pattern='y-mm-dd')
self.entry_date.grid(row=2, column=1, padx=10, pady=10)
tomorrow = datetime.now() + timedelta(days=1)
self.entry_date.set_date(tomorrow)
```

### `archive.py`

1. **Materiały pomocnicze:**
- datetime https://docs.python.org/3/library/datetime.html [14.12.2025]
- tkinter https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]
- ttk.Treeview https://docs.python.org/3/library/tkinter.ttk.html#ttk-treeview [16.01.2026]

2. **Opis kodu:**
- `__init__` - tak jak w oknach wyzej sluzy do ustawienia elementow tkinter w oknie. Dodatkowo uzywam tutaj `ttk.Treeview` do tworzenia tabelki z danymi.
- `refresh_list` - funkcja odswiezajaca dane wyswietlane w tabelce. Zbiera wszystkie egzaminy z bazy i dzieli je na 2 grupy. Aktywne, ktore sortuje rosnaco oraz przeszle, ktore sortuje malejaco. Laczy te dwie tablice w jedna i pokolei wstawia je do tabelki z odpowiednim tagiem. Dodatkowo przy wstawianiu do tabelki uzywam pola id z bazy danych aby przy zaznaczaniu egzaminu program wiedzial dokladnie ktory jest zaznaczony.
- `delete_selected` - funkcja usuwajaca zaznaczony egzamin. Rozpoznaje zaznaczenie po id i po potwierdzeniu usuwa wpis z bazy danych
- `delete_all_archive` - funkcja usuwajaca wszystkie przeszle egzaminy. Przydatna do czyszczenia bazy danych. Funkcja szuka czy sa jakiekolwiek przeszle egzaminy, jesli sa to pyta uzytkownika czy na pewno chce je usunac i po potwierdzeniu to robi
- `on_double_click` - funkcja wykonujaca sie po podwojnym kliknieciu. Szuka id egzaminu i uruchamia funkcje `open_details_window` dla wybranego egzaminu.
- `open_details_window` - funkcja otwierajaca okienko szczegolow dla wybranego egzaminu
  - `refresh_info` - funkcja odswiezajaca informacje o egzaminie po zmianach
  - `refresh_details` - zbiera tematy i wsadza je do tabelki
  - `toggle_status_local` - zmeinia status zadania "todo" / "done"
  - `edit_topic_local` - funkcja do edycji tematu. Po podwojnym kliknieciu znajduje id tematu i wywoluje funkcje edycji przekazana z `plan.py`
  - `edit_exam_local` - funkcja do edycji egzaminu. Po uruchomieniu uruchamia funkcje edycji egzaminu przekazana z `plan.py` oraz oczekuje na callback aby odswiezyc po zapisaniu zmian.

3. **Sposób pisania:**

Cała logika wyswietlania i sortowania egzaminow jest opracowana samodzielnie. Przy rozdzialniu `main.py` na poszczegolne pliki napotkalem problem z funkcjonalnoscia edycji z tego miejsca. W tym pomoglo mi Google Gemini pokazujac w jaki sposob uruchamiac funkcje znajdujace sie w innym pliku oraz pomogl z zaimplementowaniem bardziej zaawansowanej logiki callback. Nie napisal tego za mnie tylko dokladnie wytlumaczyl jak to ma dzialac w moim kodzie, a dokladniej wytlumaczyl czemu nie dziala i co trzeba zmienic.


### `edit.py`

1. **Materiały pomocnicze:**
- uuid https://docs.python.org/3/library/uuid.html [13.12.2025]
- tkcalendar https://pypi.org/project/tkcalendar/ [14.01.2026] [autor: j_4321]
- tkinter https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]

2. **Opis kodu:**
- `select_edit_item` - funkcja rozpoznajaca czy to egzamin czy temat i uruchamiajaca odpowiednia klase
- `EditExamWindow` - klasa do edycji egzaminow
  - `__init__` - otworzenie okienka z polami do wpisania nowych danych egzaminu albo poprawienie poprzednich
  - `save_changes` - zbiera dane wpisane przez uzytkownika i zapisuje je w bazie danych
  - `delete_exam` - usuwa egzamin po potwierdzeniu przez uzytkownika
- `EditTopicWindow` - klasa do edycji tematow
  - `__init__` - otworzenie okienka z polami do edycji tematow
  - `save_changes` - zbiera dane wpisane przez uzytkownika i zapisuje w bazie. Dodatkowo jesli uzytkownik recznie zmienil date to program ustawia locked na True aby `planner.py` nie zmienil jej.
  - `delete_topic` - usuwa temat po potwierdzeniu przez uzytkownika

3. **Sposób pisania:**

Kod zostal napisany samodzielnie. AI jedynie podpowiedzialo aby uzyc struktury funkcja rozpoznajaca + 2 klasy.

### `manual.py`

1. **Materiały pomocnicze:**
- tkinter - https://www.geeksforgeeks.org/python/python-gui-tkinter/ [16.01.2026] [autor: kartik]

2. **Opis kodu:**

W tym pliku tylko ustawiam wyglad okna i ustawiam pole tekstowe, do ktorego wklejam tekst z pliku jezykowego. Dodatkowo nadaje tag dla naglowka i reszty tekstu i blokuje mozliwosc edycji przez uzytkownika.

3. **Sposób pisania:**

Kod zostal napisany samodzielnie z pomoca materialu o tk.Text