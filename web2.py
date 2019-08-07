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

app = Flask(__name__)
loaded_model = None
pool = redis.ConnectionPool(host='0.0.0.0', port=8080, db=0)
embed = g = session = messages = output = None
graph_load_time=embedding_time=0




if __name__ == '__main__':
    app.run(debug=True, threaded=True,host='0.0.0.0',port='8080')
