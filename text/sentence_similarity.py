"""@author andy """
"""sentence similarity api for handling one2one,many2one,one2many and many2many """
"""before getting the sentence similarity value start the bert server using"""
"""ssh vv@xxx.xxx.xxx.xxx"""
"""source andy/venv/bin/activate"""
"""bert-serving-start -model_dir andy/tmp/multi_cased_L-12_H-768_A-12"""
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from numpy import dot
from numpy.linalg import norm
import time
from flask import jsonify
import json
import time
import os
import redis
import matplotlib.pyplot as plt
import pandas as pd
import re

def sentence_embedding_andy(sentence1, g, output, session, messages):
    input_sentences = []
    for item in sentence1:
        input_sentences.append(item)
    num_sent=len(sentence1)
    with g.as_default():
        message_embeddings = session.run(output, feed_dict={messages:input_sentences})
    sentencesEmbeddings = np.array(message_embeddings)[0:num_sent]
    return sentencesEmbeddings

def setup_all_andy(sentence1,sentence2,embed,g,session,messages,output):
    start = time.time()
    s1=sentence1
    s2=sentence2
    embeeding1=sentence_embedding_andy(s1,g,output,session, messages)
    embeeding2=sentence_embedding_andy(s2,g,output,session, messages)
    embedding_time=time.time()-start
    print("Time taken for embedding="+str(time.time() - start))
    return embeeding1,embeeding2

def use(s1,s2,embed,g,session,messages,output):
    start = time.time()
    input_sentences1=s1
    input_sentences2=s2
    v1,v2=setup_all_andy(input_sentences1,input_sentences2,embed,g,session,messages,output)
    print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("Time taken for embedding="+str(time.time() - start))
    start=time.time()
    col=len(v1)
    row=len(v2)
    mtrix=[]
    for i in range(row):
        row=[]
        for j in range(col):
            row.append(0)
        mtrix.append(row)

    for i in range(len(v2)):
        for j in range(len(v1)):
            smilarity_score=np.inner(v1[j],v2[i])/(norm(v1[j])*norm(v2[i]))
            mtrix[i][j]=smilarity_score

    arr1=[]
    for i,value1 in enumerate(input_sentences2):
        arr2=[]
        for j,value2 in enumerate(input_sentences1):
            dic={}
            dic['sentence1']=value2
            dic['sentence2']=value1
            dic['similarityScore']=str(mtrix[i][j])
            arr2.append(dic)
        arr1.append(arr2)
    print("Time taken for computing inner product="+str(time.time()-start))
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    return jsonify(arr1)

def bert(sentence1, sentence2, bc):
    result = []
    start=time.time()
    vec1 = bc.encode(sentence1)
    vec2 = bc.encode(sentence2)
    print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("time for encoding="+str(time.time()-start))
    start=time.time()
    for i in range(len(sentence2)):
        x=[]
        for j in range(len(sentence1)):
            a = vec2[i]
            b = vec1[j]
            cos_sim = dot(a, b)/(norm(a)*norm(b))
            x.append({"sentence1":sentence1[j], "sentence2":sentence2[i],"smilarity_score":str(cos_sim)})
        result.append(x)
    print("time for computing inner product="+str(time.time()-start))
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    return result
