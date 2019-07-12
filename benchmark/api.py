import psycopg2
import re

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
            d = {"id":row[0], "audio_url": row[3], "ds_trans": row[6], "real_trans": row[7], "is_verified": row[5]}
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

