from flask import Flask
from flask import request
from flask import jsonify
from flask import send_from_directory
from text import sentence_similarity as sentence_similarity_api
from speech.analysis import main as analysis_api
from speech.emotion import emotion_api
from speech.utils import misc
from speech.utils import objects
from text import emotion_detection as emotion_detection_api
import jsonpickle
import redis
from speech.transcription.transfer_learning import chunk_data_api as chunk_api
import tensorflow as tf
import tensorflow_hub as hub
import json
import uuid
from keras import backend as K
#from text import bert_mrpc as bert_api
import shutil
import os
# from benchmark import api as ds_benchmark_api
from bert_serving.client import BertClient
import numpy as np
from flask import Response
import time
app = Flask(__name__)
loaded_model = None
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
embed=g=session=messages=output=bc=None
model=None

def perform_graph_setup_andy():
    global embed,g,session,messages,output,bc
    print("Loading tensorflow graph for the first request")
    module_url="https://tfhub.dev/google/universal-sentence-encoder-large/3"
    os.environ['TFHUB_CACHE_DIR']='./tfhub'
    if os.path.exists(os.environ['TFHUB_CACHE_DIR']) and os.path.isdir(os.environ['TFHUB_CACHE_DIR']):
        shutil.rmtree(os.environ['TFHUB_CACHE_DIR'])
        os.makedirs(os.environ['TFHUB_CACHE_DIR'])
    embed = hub.Module(module_url)
    print("While first request loading hub module downloaded..")
    g = tf.get_default_graph()
    session = tf.Session(graph=g)
    session.run([tf.global_variables_initializer(), tf.tables_initializer()])
    messages = tf.placeholder(dtype=tf.string, shape=[None])

    output = embed(messages)

@app.route("/sentence_similarity",methods=["POST","GET"])
def check_smilarity_andy():
    global embed,g,session,messages,output,bc
    list1=request.form.getlist('sentence1')
    list2=request.form.getlist('sentence2')
    print(list1)
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
        start = time.time()
        if g == None:
            start=time.time()
            perform_graph_setup_andy()
            graph_load_time=time.time()-start
            print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Time taken to load graph="+str(time.time() - start))
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        return sentence_similarity_api.use(input_sentences1,input_sentences2,embed,g,session,messages,output)
    elif arg=="BERT":
        return jsonify(sentence_similarity_api.bert(input_sentences1,input_sentences2,bc))

# this service makes use of persistant tf.session so if multiple tf.sessions are opend without closing the previce ones this service will fail
# have to think a solution for that
@app.route("/emotion_detection",methods=["POST","GET"])
def emotion_dection_trainModel():
    global embed,model
    if(embed==None):
        module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
        embed=hub.Module(module_url)
    if model==None:
        model=emotion_detection_api.neural_network_setup(embed)
        session_emotion_detect = tf.Session()
        K.set_session(session_emotion_detect)
        session_emotion_detect.run(tf.global_variables_initializer())
        session_emotion_detect.run(tf.tables_initializer())
        model.load_weights('./model.h5')
    list1=request.form.getlist('sentences')
    listx=list1[0].split("[")
    listy=listx[1].split("]")
    listz=listy[0].split(",")
    input_sentences1=[]
    for item in listz:
        input_sentences1.append(item.replace('"',""))
    new_text=input_sentences1
    new_text = np.array(new_text, dtype=object)[:, np.newaxis]
    emotions_to_print = emotion_detection_api.make_prediction(new_text,model)
    return jsonify(emotions_to_print)


@app.route("/transcibe", methods=['GET', 'POST'])
def transcibe():
    task_id = request.args['task_id']
    if task_id is None:
        task_id = uuid.uuid4().hex
    task_url = misc.get_task_url(task_id)
    url = request.args.get("url")
    if url is None:
        print("URL not provided")
    else:
        task_url = url
    language = request.args['language']
    model = (request.args['model'] == 'True')
    engine = request.args['engine']
    if engine is None:
        engine = 'google'
    print('Started: '+task_id)
    conversation_blocks = analysis_api.transcribe_emotion(engine, task_id, language, model, loaded_model, pool, task_url, False)
    print('Finished: '+task_id)
    return jsonpickle.encode(conversation_blocks)

@app.route("/transcibe_emotion", methods=['GET', 'POST'])
def transcibe_emotion():
    task_id = request.args['task_id']
    if task_id is None:
        task_id = uuid.uuid4().hex
    task_url = misc.get_task_url(task_id)
    url = request.args.get("url")
    if url is None:
        print("URL not provided")
    else:
        task_url = url
    language = request.args['language']
    model = (request.args['model'] == 'True')
    engine = request.args['engine']
    if engine is None:
        engine = 'google'
    conversation_blocks = analysis_api.transcribe_emotion(engine, task_id, language, model, loaded_model, pool, task_url)
    return jsonpickle.encode(conversation_blocks)

@app.route("/emotion", methods=['GET', 'POST'])
def emotion():
    task_id = request.args['task_id']
    if task_id is None:
        task_id = uuid.uuid4().hex
    url = request.args.get("url")
    if url is None:
        print("URL not provided")
        task_url = misc.get_task_url(task_id)
    else:
        task_url = url
    global loaded_model
    if loaded_model is None:
        loaded_model = emotion_api.getModel()
        loaded_model._make_predict_function()
    emotion_blocks = analysis_api.emotion(task_url, task_id, loaded_model)
    return jsonpickle.encode(emotion_blocks)

@app.route("/emotion_stream", methods=['GET', 'POST'])
def emotion_stream():
    task_id = request.args.get("task_id")
    url = request.args.get("url")
    global loaded_model
    if loaded_model is None:
        loaded_model = emotion_api.getModel()
        loaded_model._make_predict_function()
    emotion_blocks = emotion_api.windowing_emotion(url, task_id, loaded_model)
    return jsonpickle.encode(emotion_blocks)

@app.route("/chunks", methods=['GET', 'POST'])
def chunks():
    page = request.args['page']
    pagination = request.args['pagination']
    chunks = chunk_api.fetch_chunks(page, pagination)
    return jsonpickle.encode(chunks)

@app.route("/verify_chunk", methods=['GET', 'POST'])
def verify_chunk():
    chunk_id = request.args['chunk_id']
    is_verified = request.args['is_verified'].lower().startswith('t')
    chunks = chunk_api.mark_chunk_as_verified(chunk_id, is_verified)
    return jsonpickle.encode(chunks)

@app.route("/seen_chunk", methods=['GET', 'POST'])
def seen_chunk():
    chunk_id = request.args['chunk_id']
    chunks = chunk_api.mark_chunk_as_seen(chunk_id)
    return jsonpickle.encode(chunks)

@app.route("/update_chunk_transcription", methods=['GET', 'POST'])
def update_chunk_transcription():
    chunk_id = request.args['chunk_id']
    transcript = request.args['transcript']
    print("New: "+transcript)
    chunks = chunk_api.update_chunk_transcription(chunk_id, transcript)
    return jsonpickle.encode(chunks)

@app.route('/')
def send_base():
    path = 'index.html'
    return send_from_directory('static/', path)

@app.route('/verified_chunks', methods=['GET'])
def send_verified_static():
    path = 'index2.html'
    return send_from_directory('static/', path)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/audio/<path:path>')
def send_static_audio(path):
    return send_from_directory('/home/absin/Downloads/dataset/chunks', path)

@app.route('/api/snippets/<int:count>/<int:page>')
def serve_snippet(count, page):
    data = chunk_api.fetch_verified_chunks(count, page)
    return json.dumps({'response': data})

@app.route('/dschunks/<path:path>')
def send_static_dsaudio(path):
    return send_from_directory('/home/vv/dev/ai/benchmark/chunks/', path)


@app.route('/ds_chunks/<int:count>/<int:page>')
def deepspeech_chunk_api(count, page):
    data = ds_benchmark_api.getEntries(count, page)
    return json.dumps({'response': data})

@app.route('/ds_update_real_trans/<int:chunk>')
def deepspeech_chunk_api_update_real_trans(chunk):
    real_trans = request.args['real_trans']
    ds_benchmark_api.updateRealTrans(chunk, real_trans)
    return "Done"

@app.route('/ds_update_is_verified/<int:chunk>')
def deepspeech_chunk_api_update_is_verified(chunk):
    is_verified = request.args['is_verified']
    data = ds_benchmark_api.updateIsVerified(chunk, is_verified)
    return "Done"

@app.route('/favicon.ico')
def send_fav():
    path = 'favicon.ico'
    return send_from_directory('static/assets/', path)

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5010',ssl_context='adhoc')
