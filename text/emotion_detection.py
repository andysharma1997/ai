"""@author andy"""
"""This file is used by web.py for the emotion detection using USE """
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
import re
import seaborn as sns
import keras.layers as layers
from keras.models import Model
from keras import backend as K
import psycopg2
import pandas.io.sql as sqlio
import numpy as np
import yaml
import os
import sys
embed=None
model=None
config=yaml.load(open('./constants.yaml'))
# #get the data from the db to create the the neural network
# def check_cofigs():
#     print("!!!!!!!!!!!!!!!!!!!!!!!!")
#     print(config['emotion']['frac'])

def get_dataframe_sql():
    start=time.time()
    df = None
    sql = "select emotion as label, text_ as text from dataset_emotion_only"
    con = None
    try:
        con = psycopg2.connect("host="+str(config['emotion']['db_host'])+" dbname='"+str(config['emotion']['db_dbname'])+"' user='"+str(config['emotion']['db_user'])+"' password='"+config['emotion']['db_password']+"'")
        df = sqlio.read_sql_query(sql, con)
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()
    df = df.sample(frac=config['emotion']['frac'])
    df.label = df.label.astype('category')
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("Time to fetch from db="+str(time.time()-start))
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    return df

#make the data fame for the train data and test data
def make_train_and_test_df():
    df = get_dataframe_sql()
    msk = np.random.rand(len(df)) < 0.8
    df_train = df[msk]
    df_test = df[~msk]
    category_counts = len(df_train.label.cat.categories)
    return df_train,category_counts


def UniversalEmbedding(x):
    global embed
    return embed(tf.squeeze(tf.cast(x, tf.string)), signature="default", as_dict=True)["default"]

#funtion for creating the model for prediction
#this model has one input layer,one Lambda layer,2 dense layer and 1 output layer
def neural_network_setup(emb) :
    global embed
    embed=emb
    embed_size = embed.get_output_info_dict()['default'].get_shape()[1].value
    df_train,category_counts=make_train_and_test_df()
    input_text = layers.Input(shape=(1,), dtype=tf.string)
    embedding = layers.Lambda(UniversalEmbedding, output_shape=(embed_size,))(input_text)
    dense = layers.Dense(256, activation='relu')(embedding)
    pred = layers.Dense(category_counts, activation='sigmoid')(dense)
    model = Model(inputs=[input_text], outputs=pred)
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

"""function for the pridiction of emotions it returns an array arr1 that contains
the sentences and the emotions whose thresoled is more than 0.1 that can """
def make_prediction(sentences,mod):
    global model
    df_train,category_counts=make_train_and_test_df()
    new_text=sentences
    categories = df_train.label.cat.categories.tolist()
    model=mod
    # with tf.Session() as session:
    #     K.set_session(session)
    #     session.run(tf.global_variables_initializer())
    #     session.run(tf.tables_initializer())

    predicts = model.predict(new_text,batch_size = 32)
    threshold = config['emotion']['threshold']
    arr1=[]
    for i,sentence in enumerate(new_text):
        predict = predicts[i]
        dic1={}
        dic1["sentence"+str(i+1)]=sentence[0]
        dic2={}
        for j, pred in enumerate(predict):
            if pred>threshold:
                dic2[categories[j]]=str(pred)
            dic1["emotions"]=dic2
        arr1.append(dic1)
    return arr1
