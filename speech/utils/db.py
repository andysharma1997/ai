import sys
from os import path
import os
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
import psycopg2
from speech.utils import constants

def execute_query(sql):
    rows = []
    colnames = None
    con = None
    try:
        con = psycopg2.connect("host='"+constants.fetch_contant_single('host')+
            "' dbname='sales' user='postgres' password='"+constants.fetch_contant_single('password')+"'")
        cur = con.cursor()
        cur.execute(sql)
        if colnames == None:
            colnames = [desc[0] for desc in cur.description]
        while True:
            row = cur.fetchone()
            if row == None:
                break
            rows.append(row)
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()
    return rows, colnames
