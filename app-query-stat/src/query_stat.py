#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: huberp

library management - query statistics
"""

import pika, sys, os, mysql.connector, json, re, datetime

cnx = None
rabbitmq_url = None

def main():
    global cnx, rabbitmq_url
    ROUTE = 'query_stat'

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

    print(' [*] Library stat query service. Waiting for message. To exit press CTRL+C')

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()

def callback(ch, method, properties, body):
    # TODO - authenticate message
    # TODO - validate message

    query = json.loads(body)

    cmd = 'SELECT * FROM stat'
    cursor = cnx.cursor()
    cursor.execute(cmd)
    result = cursor.fetchall()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange='library', exchange_type='direct')
    channel.basic_publish(exchange='library', routing_key='query_stat_result', body=json.dumps(result, default=default_date))
    connection.close()
    print(" [x] Sent %r" % (result,))

    ch.basic_ack(delivery_tag = method.delivery_tag)

def default_date(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

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
