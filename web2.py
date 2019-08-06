"""@author andy """
"""sentence similarity api for handling one2one,many2one,one2many and many2many """
"""before getting the sentence similarity value start the bert server using"""
"""ssh vv@xxx.xxx.xxx.xxx"""
"""source andy/venv/bin/activate"""
"""bert-serving-start -model_dir andy/tmp/multi_cased_L-12_H-768_A-12"""
from bert_serving.client import BertClient
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
import numpy as np
from flask import Flask
from flask import request
from flask import jsonify
bc = BertClient(ip='192.168.0.199')
app = Flask(__name__)
loaded_model = None
pool = redis.ConnectionPool(host='0.0.0.0', port=8080, db=0)
embed = g = session = messages = output = None
graph_load_time=embedding_time=0

def sentence_embedding_andy(sentence1, g, output, session, messages):
    input_sentences = []
    for item in sentence1:
        input_sentences.append(item)
    num_sent=len(sentence1)
    with g.as_default():
        message_embeddings = session.run(output, feed_dict={messages:input_sentences})
    sentencesEmbeddings = np.array(message_embeddings)[0:num_sent]
    return sentencesEmbeddings

def perform_graph_setup_andy():
    global embed,g,session,messages,output
    print("Loading tensorflow graph for the first request")
    module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
    os.environ['TFHUB_CACHE_DIR']='/home/andy/tfhub'
    #if os.path.exists(os.environ['TFHUB_CACHE_DIR']) and os.path.isdir(os.environ['TFHUB_CACHE_DIR']):
    #    shutil.rmtree(os.environ['TFHUB_CACHE_DIR'])
    #os.makedirs(os.:['TFHUB_CACHE_DIR'])
    embed = hub.Module(module_url)
    print("While first request loading hub module downloaded..")
    g = tf.get_default_graph()
    session = tf.Session(graph=g)
    session.run([tf.global_variables_initializer(), tf.tables_initializer()])
    messages = tf.placeholder(dtype=tf.string, shape=[None])
    output = embed(messages)
    print('Successfully initialized sentence similarity variables')

def setup_all_andy(sentence1,sentence2):
    global embed,g,session,messages,output,graph_load_time,embedding_time
    if g == None:
        start=time.time()
        perform_graph_setup_andy()
        graph_load_time=time.time()-start
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("Time taken to load graph="+str(graph_load_time))
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    s1=sentence1
    s2=sentence2
    start1=time.time()
    embeeding1=sentence_embedding_andy(s1,g,output,session, messages)
    embeeding2=sentence_embedding_andy(s2,g,output,session, messages)
    embedding_time=time.time()-start1
    return embeeding1,embeeding2

def use_sentence_similarity_andy(s1,s2):
    global graph_load_time,embedding_time
    input_sentences1=s1
    input_sentences2=s2
    v1,v2=setup_all_andy(input_sentences1,input_sentences2)
    print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("Time taken for embedding="+str(embedding_time))
    start1=time.time()
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
            smilarity_score=np.inner(v1[j],v2[i])
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
    print("Time taken for computing inner product="+str(time.time()-start1))
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    return jsonify(arr1)


def cosine_similarity_andy(sentence1, sentence2):
    result = []
    start=time.time()
    vec1 = bc.encode(sentence1)
    vec2 = bc.encode(sentence2)
    print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("time for encoding="+str(time.time()-start))
    start1=time.time()
    for i in range(len(sentence2)):
        x=[]
        for j in range(len(sentence1)):
            a = vec2[i]
            b = vec1[j]
            cos_sim = dot(a, b)/(norm(a)*norm(b))
            x.append({"sentence1":sentence1[j], "sentence2":sentence2[i],"smilarity_score":str(cos_sim)})
        result.append(x)
    print("time for computing inner product="+str(time.time()-start1))
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    return result

@app.route("/many2many_newform",methods=["POST","GET"])
def check_smilarity_andy():
    list1=request.form.getlist('sentence1')
    list2=request.form.getlist('sentence2')
    arg=request.args.get('model')
    listx=list1[0].split("[")
    listy=listx[1].split("]")
    listz=listy[0].split(",")
    input_sentences1=[]
    for item in listz:
        input_sentences1.append(item.replace('"',""))

    listx1=list2[0].split("[")
    listy1=listx1[1].split("]")
    listz1=listy1[0].split(",")
    input_sentences2=[]
    for item in listz1:
        input_sentences2.append(item.replace('"',""))

    if arg == "USE":
        return use_sentence_similarity_andy(input_sentences1,input_sentences2)
    elif arg=="BERT":
        return jsonify(cosine_similarity_andy(input_sentences1,input_sentences2))


if __name__ == '__main__':
    app.run(debug=True, threaded=True,host='0.0.0.0',port='8080')
