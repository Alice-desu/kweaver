# -*-coding:utf-8-*-

import sys
import os
# sys.path.append(os.path.abspath("../../util"))
from utils.pymysql_pool import PymysqlPool
import pymysql

db_type = "docker_db"


def connect_execute_commit_close_db(func):
    def wrapper(*args, **kwargs):
        pymysql_pool = PymysqlPool.get_pool()
        connection = pymysql_pool.connection()
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        kwargs['connection'] = connection
        kwargs['cursor'] = cursor
        try:
            ret = func(*args, **kwargs)
            connection.commit()
            return ret
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
        return None

    return wrapper


def connect_execute_close_db(func):
    def wrapper(*args, **kwargs):
        pymysql_pool = PymysqlPool.get_pool()
        connection = pymysql_pool.connection()
        kwargs['connection'] = connection
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        kwargs['cursor'] = cursor
        try:
            ret = func(*args, **kwargs)
            return ret
        except Exception as e:
            raise e
        finally:
            cursor.close()
            connection.close()
        return None

    return wrapper
