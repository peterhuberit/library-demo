#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: huberp

konyvtar menedzsment - konyv lekerdezes
"""

import pika, sys, os, mysql.connector, json, re

cnx = None

def main():
    global cnx
    ROUTE = 'query_book'

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

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange='library', exchange_type='direct')
    result = channel.queue_declare(queue='', exclusive=True, durable=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='library', queue=queue_name, routing_key=ROUTE)

    print(' [*] Library book query service. Waiting for message. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

def callback(ch, method, properties, body):
    # TODO - authenticate message
    # TODO - validate message

    query = json.loads(body)

    cmd = '''SELECT * FROM book
        WHERE
        title LIKE %s
        AND author LIKE %s
        AND publisher LIKE %s
        AND publishing_date LIKE %s
        AND date_of_listing LIKE %s
        AND (number_of_copies = %s OR -1 = %s)
        '''

    columns = ('title', 'author', 'publisher', 'publishing_date', 'date_of_listing', 'number_of_copies')
    for k in columns:
        if k not in query.keys():
            query[k] = ''

    query['number_of_copies'] = -1 if type(query['number_of_copies']) is str else query['number_of_copies']

    cursor = cnx.cursor(prepared=True)
    params = ('%'+query['title']+'%', '%'+query['author']+'%', '%'+query['publisher']+'%', '%'+query['publishing_date']+'%', '%'+query['date_of_listing']+'%', query['number_of_copies'], query['number_of_copies'])
    cursor.execute(cmd, params)
    result = cursor.fetchall()
    print('RESULT: ', result)
    # TODO - publish result on RabbitMQ?

    ch.basic_ack(delivery_tag = method.delivery_tag)

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