# Könyvtárnyilvántartó demo alkalmazás
## Python service alkalmazás RabbitMQ, Docker, Kubernetes és Helm Chart alapokon

Az alkalmazás három különálló service-ból áll, ezek az app-add-book, app-query-book, app-query-stat (ld. az ilyen nevű foldereket), python3-ban írva.

### Felépítés
Az egyes service-ok alapvetően a RabbitMQ message broker-t használják a belső kommunikációra, illetve MySQL (5.7) adatbázist az adatok tárolására.

### Service-ok
#### add_book/src/add_book.py
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

#### query_book/src/query_book.py
A könyvek keresésére szolgáló service, a message brokeren keresztül a _library_ exchange _query_book_ route-jára vár json adatot, például:
```json
{
    "title": "Guide",
    "author": "Douglas Adams"
}
```

#### query_stat/src/query_stat.py
A könyvekről készült tárolt statisztikák lekérdezésére szolgáló service. A message brokeren keresztül a _library_ exchange _query_stat_ route-jára vár bármilyen json adatot.

### Docker
#### Docker konténerek létrehozása
A python alkalmazások konténerizációja a python:3.8-slim-buster image-en alapul, ez egy relatív "lightweight" python image. 
A következő parancsokat kell futtatni az egyes konténerek létrehozásához, és Docker Hub-ba feltöltéséhez az alkalmazás folderében futtatva:
```
#add_book/:
docker build -t add_book.library .
docker tag add_book.library:latest <DOCKER_ID>/add_book.library:latest
docker push peterhuber/add_book.library:latest

#query_book/:
docker build -t query_book.library .
docker tag query_book.library:latest <DOCKER_ID>/query_book.library:latest
docker push peterhuber/query_book.library:latest

#query_stat/:
docker build -t query_stat.library .
docker tag query_stat.library:latest <DOCKER_ID>/query_stat.library:latest
docker push peterhuber/query_stat.library:latest
```

#### Kubernetes, Helm
Az alkalmazás Helm chart-ja library-helm-chart/ folder-ben találhatóak, a python service-ok mellett a RabbitMQ és a MySQL Kubernetes konfigjai is itt vannak. Ehhez a demóhoz egyedül a MySQL jelszavát raktam ki a library-helm-chart/values.yaml-be.


