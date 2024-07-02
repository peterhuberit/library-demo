# Library Management Demo Application
## Containerized Python Service Application Based on RabbitMQ, MySQL, Docker, Kubernetes, and Helm Chart
The application consists of three separate services: app-add-book, app-query-book, app-query-stat (see folders with these names), written in Python 3.

### Structure
Each service primarily uses the RabbitMQ message broker for internal communication and MySQL (5.7) database for data storage.

### Services
#### app-add-book/src/add_book.py
This service is responsible for registering new books and updating stored statistics about books. It waits for JSON data on the _library_ exchange _add_book_ route via the message broker, for example:
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
The data is saved in the _book_ table of _library_ schema.

#### app-query-book/src/query_book.py
This service is used for searching books, waiting for JSON data on the _query_book_ route of _library_ exchange via the message broker, for example:
```json
{
    "title": "Guide",
    "author": "Douglas Adams"
}
```
The service sends the results retrieved from the _book_ table to the _query_book_result_ route of _library_ exchange in JSON format.

#### app-query-stat/src/query_stat.py
This service is used for querying stored statistics about books. It waits for any JSON formatted data (e.g., {}) on the _query_stat_ route of library exchange via the message broker. It returns the entire contents of the stat table. The table records contain various statistics about the library, e.g.:
```
stat_label         |  stat_value
book_by_author     |  [["Douglas Adams", "14"], ["William Gibson", "32"]]
book_by_publisher  |  [["Bantam Spectra", "15"], ["Pan Books", "14"], ["Victor Gollancz Ltd", "17"]]
```
The service sends the results retrieved from the _stat_ table to the _query_stat_result_ route of _library_ exchange in JSON format.

### Docker
#### Creating Docker Containers
The containerization of Python applications is based on the python:3.8-slim-buster image, which is a relatively "lightweight" Python image. The following commands need to be run to create the containers and upload them to Docker Hub, executed in the application folder:
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
Kubernetes, Helm
The application's Helm chart is located in the library-helm-chart/ folder, along with the Kubernetes configurations for RabbitMQ and MySQL. For this demo, only the MySQL password is set in the library-helm-chart/values.yaml.

Install:
```
helm install library-install library-helm-chart/
```

When testing with Minikube, the following command is also necessary to access the RabbitMQ management interface:
```
minikube service rabbitmq-service
```

### Local Development
#### RabbitMQ:
RabbitMQ needed for development can be started from a Docker image on the developer machine:
```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
In this case, the management interface is accessible at http://localhost:15672.

#### Database
To access the database, the configuration of each Python service needs to be modified:
that is, appropriately fill out the _app-add-book|app-query-book|app-query-stat/src/config/cnf.json.DIST_ files and save them as cnf.json.

#### Starting services
```
cd app-add-book/src && python3 add_book.py
cd app-query-book/src && python3 query_book.py
cd app-query-stat/src && python3 query_stat.py
```

### Test Data
The services can be accessed via RabbitMQ messages, which can also be tested through the management interface:

#### Adding a Book:
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

#### Searching for a Book:
exchange: library
routing: query_book
example payload:
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

#### Querying Statistics:
exchange: library
routing: query_stat
payload: ```{}```

Valid messages received will always log to the console by each service.

