#!/usr/bin/env python
# coding: utf-8

# Here we are going to benchmark [mozilla's deepspeech](https://github.com/mozilla/DeepSpeech). The release claims that deepspeech works on American English achieving an 8.22% word error rate on the LibriSpeech clean test corpus.
# Now, since we happen to have ~ 50 hours of american english phone conversation recordings  we can attempt to benchmark how well deepspeech works in production.
# So this is what we are going to do:
# * We will take the call recordings and remove the agent channel (we have 2 channels, one corresponds to the agent and the other to the customer)
# * We will split the recordings based on voice activity (so one continuous segment of audio will become one chunk)
# * We will transcribe these chunks using deepspeech
# * We will then manually transcribe them. In order to manually transcribe we will develop our own web browser based interface to perform manual transcription of these chunks. 
# * We will then implement the WER algorithm to compute WERs across the chunks which have been manually transcribed
# * Observe the system live

# In[1]:


import sys
from os import path
import os
current_folder = (os.path.abspath(''))
root_path = path.dirname(current_folder)
sys.path.append(root_path)
from speech.utils import misc
from speech.utils import vad
from speech.utils import constants
from speech.transcription import deep_speech_api
import psycopg2
import re
import soundfile as sf
from deepspeech import Model, printVersions
import time
from jiwer import wer


# In[2]:


BENCH_PATH=root_path+'/benchmark/'
CHUNK_PATH=BENCH_PATH+'chunks/'
TASK_PATH=BENCH_PATH+'tasks/'
CUST_PATH=BENCH_PATH+'tasks_cust/'

# These constants control the beam search decoder
# Beam width used in the CTC decoder when building candidate transcriptions
BEAM_WIDTH = 500
# The alpha hyperparameter of the CTC decoder. Language Model weight
LM_ALPHA = 0.75
# The beta hyperparameter of the CTC decoder. Word insertion bonus.
LM_BETA = 1.85
# These constants are tied to the shape of the graph used (changing them changes
# the geometry of the first layer), so make sure you use the same constants that
# were used during training
# Number of MFCC features to use
N_FEATURES = 26
# Size of the context window used for producing timesteps in the input vector
N_CONTEXT = 9

# ### Download audio

# In[3]:


"""
All our task recirdings are stored on a google storage bucket, using this method we will download these files
It returns an object {"abs_path": "/home/vv/dev/ai/benchmark/tasks/12654.wav", "success": true}
"""
def downloadTaskAudio(taskId):
    downloadResult = misc.download_file(misc.get_task_url(taskId), TASK_PATH)
    return downloadResult


# ### Remove agent channel

# In[4]:


"""
Remove the agent  channel from the supplied dual channel audio and return the path of the customer's channel
"""
def removeAgentChannel(dualChannelAudioPath):
    splits = misc.split_stereo(dualChannelAudioPath, CUST_PATH)
    # assuming the right is customer which is _2.wav we keep that and delete the _1.wav
    os.remove(splits[0])
    return splits[1]


# ### Perform VAD

# In[5]:


"""
We perform VAD (Voice activity detection) on the audio and split it to many chunks here.
The method then returns the path of these chunks as a list
"""
def performVAD(audioFilePath):
    snippets = vad.perform_vad(audioFilePath, CHUNK_PATH, min_chunk_length=1, max_chunk_length=50)
    print('For file: '+audioFilePath+', total chunks produced -->'+str(len(snippets)))
    return snippets


# ### Transcribe using DeepSpeech

# In[6]:


"""
We use deepspeech's python API to perform transcription here
"""
"""
We implement WER algorithm here
"""
def transcribe(audioFilePath, ds):
    transcript = deep_speech_api.main(True, audioFilePath, ds)
    return transcript


# ### Compute WER

# In[7]:


"""
We implement WER algorithm here
"""
def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

def cer(realTranscription, deepspeechTranscription):
    return levenshtein(realTranscription.lower(), deepspeechTranscription.lower())/len(realTranscription) 


# In[8]:


def fetchTaskIds():
    taskIds = []
    sql = 'select * from task where "owner" = 198359;'
    con = None
    try:
        con = psycopg2.connect("host='192.168.0.102' dbname='sales' user='postgres' password='root'")
        cur = con.cursor()
        cur.execute(sql)
        while True:
            row = cur.fetchone()
            if row == None:
                break
            taskIds.append(row[0])
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()
    return taskIds


# In[9]:


"""
In this method we will ubsample the audio at given path then replace it with the upsampled audio
"""
def upsampleAudio(audioPath, sr):
    data, samplerate = sf.read(audioPath)
    sf.write(audioPath, data, sr)
    return audioPath


# In[10]:


def main():
    start = time.time()
    model_path = constants.fetch_contant('deepspeech', 'model_path')
    alphabet_path = constants.fetch_contant('deepspeech', 'alphabet_path')
    print('Loading model from file {}'.format(model_path), file=sys.stderr)
    ds = Model(model_path, N_FEATURES, N_CONTEXT, alphabet_path, BEAM_WIDTH)
    print('Loaded accoustic model after: '+str((time.time())-start), file=sys.stderr)
    lm_path = constants.fetch_contant('deepspeech', 'lm_path')
    trie_path = constants.fetch_contant('deepspeech', 'trie_path')
    print('Loading language model from files {} {}'.format(lm_path, trie_path), file=sys.stderr)
    ds.enableDecoderWithLM(alphabet_path, lm_path, trie_path, LM_ALPHA, LM_BETA)
    print('Loaded language model after: '+str((time.time())-start), file=sys.stderr)
    misc.reset_folders([CHUNK_PATH, TASK_PATH, CUST_PATH])
    con = None
    try:
        con = psycopg2.connect("host='192.168.0.102' dbname='sales' user='postgres' password='root'")
        cur = con.cursor()
        sql = 'delete from benchmark_deepspeech'
        cur.execute(sql)
        con.commit()
        print('Fetching tasks...')
        taskIds = fetchTaskIds()
        print('Fetched '+str(len(taskIds))+' tasks!')
        for taskId in taskIds:
            print('Started '+str(taskId))
            try:
                downloadResult = downloadTaskAudio(str(taskId))
                if downloadResult["success"]:
                    customerPath = removeAgentChannel(downloadResult["abs_path"])
                    #customerPath = upsampleAudio(customerPath, 16000)
                    snippets = performVAD(customerPath)
                    for snippet in snippets:
                        text = transcribe(snippet.path, ds)
                        text = re.sub("'","''",text)
                        url = 'http://192.168.0.100:5010/dschunks/'+re.sub(CHUNK_PATH,'',snippet.path)
                        sql = "INSERT INTO public.benchmark_deepspeech (created_at, updated_at, audio_url, "
                        sql += "audio_path, is_verified, ds_transcription, real_transcription, cer, wer, task_id, from_time,"
                        sql += " to_time) VALUES(now(), now(), '"+url+"', '"+snippet.path+"', false, '"+text+"', NULL, NULL, "
                        sql += "NULL, "+str(taskId)+", "+str(snippet.from_time)+", "+str(snippet.to_time)+");"
                        print(sql)
                        cur.execute(sql)
                        con.commit()
            except Exception as e:
                print(e)
            print('Finished '+str(taskId))
            #break
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        sys.exit(1)
    finally:
        if con:
            con.close()


# create table
# 	public.benchmark_deepspeech (id serial primary key,
# 	created_at timestamp,
# 	updated_at timestamp,
# 	audio_url varchar(255),
# 	audio_path varchar(255),
# 	is_verified boolean,
# 	ds_transcription varchar(2000),
# 	real_transcription varchar(2000),
# 	cer float,
# 	wer float,
# 	task_id int4,
# 	from_time float,
# 	to_time float)

# In[11]:

if __name__ == "__main__":
    main()

