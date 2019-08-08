import psycopg2
import re
from jiwer import wer
import sys
from os import path
import os
current_folder = (os.path.abspath(''))
root_path = path.dirname(current_folder)
sys.path.append(root_path)
from notebooks import BenchmarkDeepspeech as bd

def getEntries(count, page):
    ssql = 'select * from benchmark_deepspeech order by id asc limit '+str(count)+' offset '+str((page-1)*count)
    data = []
    con = None
    try:
        con = psycopg2.connect("host='192.168.0.102' dbname='sales' user='postgres' password='root'")
        cur = con.cursor()
        cur.execute(ssql)
        while True:
            row = cur.fetchone()
            if row == None:
                break
            d = {"id":row[0], "audio_url": row[3], "ds_trans": row[6], "real_trans": row[7], "is_verified": row[5], "wer":row[9], "cer":row[8]}
            data.append(d)
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()
    return data


def executeUpdate(sql):
    con = None
    try:
        con = psycopg2.connect("host='192.168.0.102' dbname='sales' user='postgres' password='root'")
        cur = con.cursor()
        cur.execute(sql)
        con.commit()
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()

def updateIsVerified(chunk, is_verified):
    sql =  'update benchmark_deepspeech set is_verified = '+is_verified+' where id = '+str(chunk)
    executeUpdate(sql)

def updateRealTrans(chunk, real_trans):
    real_trans = re.sub("'","''",real_trans)
    sql = "update benchmark_deepspeech set real_transcription = '"+real_trans+"' where id = "+str(chunk)
    executeUpdate(sql)

def computeER(chunkId=None):
    sql = "select * from benchmark_deepspeech where is_verified = true"
    if chunkId != None:
       sql = "select * from benchmark_deepspeech where id = "+str(chunkId)
    try:
        con = psycopg2.connect("host='192.168.0.102' dbname='sales' user='postgres' password='root'")
        cur = con.cursor()
        cur.execute(sql)
        cur2 = con.cursor()
        while True:
            row = cur.fetchone()
            if row == None:
                break
            d = {"id":row[0], "audio_url": row[3], "ds_trans": row[6], "real_trans": row[7], "is_verified": row[5], "wer":row[9], "cer":row[8]}
            if len(row[7]):
                cer = bd.cer(d["real_trans"],d["ds_trans"])
                weri= wer(d["real_trans"],d["ds_trans"])
                updateSql = "update benchmark_deepspeech set cer = "+str(cer)+", wer = "+str(weri)+" where id = "+str(d["id"])
                cur2.execute(updateSql)
                print(updateSql)
                con.commit()
            else:
                continue
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()
