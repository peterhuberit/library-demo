#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: huberp

konyvtar menedzsment - konyv hozzaadas
"""

import pika, sys, os, mysql.connector, json, re

cnx = None

def main():
    global cnx
    ROUTE = 'add_book'

    if os.path.exists(os.path.join('config','cnf.json')):
        with open(os.path.join('config','cnf.json'), 'r') as data:
            cnf = json.load(data)
    else:
        with open(os.path.join('config','cnf.json.DIST'), 'r') as data:
            cnf = json.load(data)

    db_user = cnf['db_user']
    db_pwd  = os.getenv('MYSQL_ROOT_PASSWORD', cnf['db_pwd'])
    db_host = os.getenv('MYSQL_URL', cnf['db_host'])
    db      = cnf['db']

    cnx = get_cnx(db_user, db_pwd, db_host, db)

    rabbitmq_url = os.getenv('RABBITMQ_SERVICE_SERVICE_HOST', 'localhost')

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange='library', exchange_type='direct')
    result = channel.queue_declare(queue='', exclusive=True, durable=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='library', queue=queue_name, routing_key=ROUTE)

    print(' [*] Library book insert service. Waiting for message. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()


def callback(ch, method, properties, body):
    print(" [x] %r: %r" % (method.routing_key, body), flush=True)

    book = json.loads(body)
    # TODO - authenticate message
    # TODO - validate message
    # TODO - ha mar van sor, ugyanazzal az title, author es published ertekekkel, akkor dobja el vagy update-elje?
    cmd = 'INSERT INTO book (title, author, publisher, publishing_date, date_of_listing, number_of_copies) VALUES (%s,%s,%s,%s,%s,%s);'
    cursor = cnx.cursor(prepared=True)
    params = (book['title'], book['author'], book['publisher'], book['publishing_date'], book['date_of_listing'], book['number_of_copies'])
    cursor.execute(cmd, params)
    cnx.commit()

    update_stats()

    ch.basic_ack(delivery_tag = method.delivery_tag)


def update_stats():
    querys = {
        'book_by_author': "SELECT author as grouper, SUM(number_of_copies) AS val FROM book GROUP BY author;",
        'book_by_publisher': "SELECT publisher as grouper, SUM(number_of_copies) AS val FROM book GROUP BY publisher;",
        'book_average_age': "SELECT AVG(DATEDIFF(NOW(), publishing_date)) AS val FROM book;",
        'book_newest': "SELECT 'id', id FROM book ORDER BY publishing_date DESC LIMIT 1;",
        'book_oldest': "SELECT 'id', id FROM book ORDER BY publishing_date LIMIT 1;",
        'book_until_year_2015': "SELECT author, COUNT(*) FROM book WHERE date_of_listing < '2015-01-01 00:00:00' GROUP BY author;",
        'book_average_listing_time_after_publish': "SELECT author, AVG(DATEDIFF(date_of_listing, publishing_date)) FROM book GROUP BY author;",
        'book_number_of_copies_3rd_by_author': """
            SELECT a.author,
                (
                    SELECT b.number_of_copies
                    FROM book b
                    WHERE b.author = a.author
                    ORDER BY publishing_date
                    LIMIT 2,1
                ) as number_of_copies,
                (
                    SELECT b.title
                    FROM book b
                    WHERE b.author = a.author
                    ORDER BY publishing_date
                    LIMIT 2,1
                ) as title
            FROM book a
            GROUP BY a.author
        """
    }

    cmd = 'DELETE FROM stat;'
    cursor = cnx.cursor()
    cursor.execute(cmd)
    cnx.commit()

    for k, query in querys.items():
        cursor = cnx.cursor(prepared=True)
        cursor.execute(query)
        result = cursor.fetchall()

        cmd = 'INSERT INTO stat (stat_label, stat_value) VALUES (%s,%s);'
        cursor = cnx.cursor(prepared=True)
        params = (k, json.dumps(result))
        cursor.execute(cmd, params)
        cnx.commit()


def get_cnx(db_user, db_pwd, db_host, db):
    return mysql.connector.connect(user=db_user,
              password=db_pwd,
              host=db_host,
              database=db,
              charset='utf8',
              use_unicode=True,
              use_pure=True)


if __name__ == '__main__':
    main()