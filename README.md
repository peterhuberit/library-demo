# Könyvtárnyilvántartó demo alkalmazás
## Konténerizált python service alkalmazás RabbitMQ, MySQL, Docker, Kubernetes és Helm Chart alapokon

Az alkalmazás három különálló service-ból áll, ezek az app-add-book, app-query-book, app-query-stat (ld. az ilyen nevű foldereket), python3-ban írva.

### Felépítés
Az egyes service-ok alapvetően a RabbitMQ message broker-t használják a belső kommunikációra, illetve MySQL (5.7) adatbázist az adatok tárolására.

### Service-ok
#### app-add-book/src/add_book.py
Ez a sevice felel az új könyvek nyílvántartásba vételéért, illetve a könyvekről készült tárolt statisztikák frissítéséért.
A message brokeren keresztül a _library_ exchange _add_book_ route-jára vár json adatot, például:
```json
{
    "title": "The Hitchhiker's Guide to the Galaxy",
    "author": "Douglas Adams",
    "publisher": "Pan Books",
    "publishing_date": "1979-01-01",
    "date_of_listing": "2020-02-04",
    "number_of_copies": 5
}
```

Az adatok a _library_ schema _book_ táblájába mentődnek.

#### app-query-book/src/query_book.py
A könyvek keresésére szolgáló service, a message brokeren keresztül a _library_ exchange _query_book_ route-jára vár json adatot, például:
```json
{
    "title": "Guide",
    "author": "Douglas Adams"
}
```
A service a _book_ táblából lekérdezett találatokat a _library_ exchange _query_book_result_ route-jára küldi json formátumban.

#### app-query-stat/src/query_stat.py
A könyvekről készült tárolt statisztikák lekérdezésére szolgáló service. A message brokeren keresztül a _library_ exchange _query_stat_ route-jára vár bármilyen json formátumú adatot (pl.: {}). A stat tábla teljes tartalmát visszaadja. A tábla az egyes rekordjai a könyvtár különböző statisztikáit tartalmazzák, pl.:
```
stat_label         |  stat_value
book_by_author     |  [["Douglas Adams", "14"], ["William Gibson", "32"]]
book_by_publisher  |  [["Bantam Spectra", "15"], ["Pan Books", "14"], ["Victor Gollancz Ltd", "17"]]
```
A service a _stat_ táblából lekérdezett találatokat a _library_ exchange _query_stat_result_ route-jára küldi json formátumban.

### Docker
#### Docker konténerek létrehozása
A python alkalmazások konténerizációja a python:3.8-slim-buster image-en alapul, ez egy relatív "lightweight" python image. 
A következő parancsokat kell futtatni az egyes konténerek létrehozásához, és Docker Hub-ba feltöltéséhez az alkalmazás folderében futtatva:
```
#app-add-book/:
docker build -t add_book.library .
docker tag add_book.library:latest <DOCKER_ID>/add_book.library:latest
docker push peterhuber/add_book.library:latest

#app-query-book/:
docker build -t query_book.library .
docker tag query_book.library:latest <DOCKER_ID>/query_book.library:latest
docker push peterhuber/query_book.library:latest

#app-query-stat/:
docker build -t query_stat.library .
docker tag query_stat.library:latest <DOCKER_ID>/query_stat.library:latest
docker push peterhuber/query_stat.library:latest
```

#### Kubernetes, Helm
Az alkalmazás Helm chart-ja library-helm-chart/ folder-ben találhatóak, a python service-ok mellett a RabbitMQ és a MySQL Kubernetes konfigjai is itt vannak. Ehhez a demóhoz egyedül a MySQL jelszavát raktam ki a library-helm-chart/values.yaml-be.

Install:
```
helm install library-install library-helm-chart/
```

Minikube-ban tesztelve a RabbitMQ menedzsment felületének eléréséhez a következő parancs is szükséges:
```
minikube service rabbitmq
```


#### Fejlesztés lokálban
##### RabbitMQ:
A fejlesztéshez szükséges RabbitMQ-t docker image-ből is lehet indítani a fejlesztői gépen:
```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
Ebben az esetben a menedzsment felület a http://localhost:15672 címen érhető el.

##### Adatbázis
Az adatbázis eléréséhez szükséges az egyes python service-ok konfigjának a módosítása:
azaz a _app-add-book|app-query-book|app-query-stat/src/config/cnf.json.DIST_ fájlok értelemszerű kitöltése és mentés cnf.json néven

##### service-ek indítása
```
cd app-add-book/src && python3 add_book.py
cd app-query-book/src && python3 query_book.py
cd app-query-stat/src && python3 query_stat.py
```


#### Tesztadatok
A service-okat a RabbitMQ message-eken keresztül lehet elérni, teszteléshez a menedzsment felületen keresztül is:

##### Könyv hozzáadása:
exchange: library
routing: add_book
payload:
```
{
    "title": "The Hitchhiker's Guide to the Galaxy",
    "author": "Douglas Adams",
    "publisher": "Pan Books",
    "publishing_date": "1979-01-01",
    "date_of_listing": "2020-02-03",
    "number_of_copies": 3
}
```

##### Könyv keresése:
exchange: library
routing: query_book
példa payload:
```
{
    "title": "",
    "author": "Douglas",
    "publisher": "",
    "publishing_date": "",
    "date_of_listing": "",
    "number_of_copies": 2
}
```

##### Statisztikák lekérdezése:
exchange: library
routing: query_stat
payload: ```{}```

A beérkezett és érvényes üzenetekre a konzolba minden esetben írnak log-ot az egyes service-ok.


