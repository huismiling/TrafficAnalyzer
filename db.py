import threading
import time

# import pymysql
import sqlite3

import config
import util

db_instances = []

def get_db_instance():
    # instance = pymysql.connect(**config.mysql_settings)
    instance = sqlite3.connect(**config.sqlite_settings)
    return instance


sqls = []
lock = threading.Lock()

def query(sql, callback=None):
    global sqls
    lock.acquire()
    sqls.append((sql, callback))
    lock.release()


def autocommit():
    if len(sqls):
        database = get_db_instance()
        cursor = database.cursor()
        print("[DB] auto commit {} sqls".format(len(sqls)))
        lock.acquire()
        _sqls = sqls.copy()
        sqls.clear()
        lock.release()

        for sql in _sqls:
            try:
                cursor.execute(sql[0])
                if sql[1] is not None:
                    sql[1](cursor.lastrowid)
            except Exception as e:
                print("[DB]", e)

        data = cursor.fetchall()
        database.close()


def close():
    for _database in db_instances:
        _database.commit()
        _database.close()


def get_time():
    return int(time.time())


def init_database():
    database = get_db_instance()
    cursor = database.cursor()

    init_dns_sql = '''CREATE TABLE IF NOT EXISTS "log_dns" (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          type mediumint(9) DEFAULT NULL,
          client_mac varchar(17) DEFAULT '',
          domain varchar(255) DEFAULT NULL,
          rdata varchar(255) DEFAULT NULL,
          time bigint(20) DEFAULT NULL
        );'''

    init_netflow_sql = '''CREATE TABLE IF NOT EXISTS "log_netflow" (
          "id" INTEGER PRIMARY KEY AUTOINCREMENT,
          "client_mac" varchar(17) DEFAULT '',
          "ip_src" varchar(15) DEFAULT NULL,
          "ip_dst" varchar(15) DEFAULT NULL,
          "port_src" mediumint(9) DEFAULT NULL,
          "port_dst" mediumint(9) DEFAULT NULL,
          "time_start" bigint(20) DEFAULT NULL,
          "time_end" bigint(20) DEFAULT NULL,
          "len" int(11) DEFAULT NULL,
          "pkt_list" mediumtext DEFAULT NULL,
          "type" tinyint(4) DEFAULT NULL,
          "host" varchar(255) DEFAULT NULL
        ) ;'''

    init_app_sql = '''CREATE TABLE IF NOT EXISTS "log_app" (
          "id" INTEGER PRIMARY KEY AUTOINCREMENT,
          "client_mac" varchar(17) DEFAULT NULL,
          "app_name" varchar(64) DEFAULT '',
          "start_time" bigint(20) DEFAULT NULL,
          "end_time" bigint(20) DEFAULT NULL,
          "host" varchar(64) DEFAULT NULL
        ); '''

    # cursor.execute('SET GLOBAL SQL_MODE=ANSI_QUOTES;')
    cursor.execute(init_dns_sql)
    cursor.execute(init_netflow_sql)
    cursor.execute(init_app_sql)
    data = cursor.fetchall()
    database.close()


init_database()
util.add_cron(autocommit, 1)
