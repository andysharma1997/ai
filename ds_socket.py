import asyncio
import websockets
from deepspeech import Model, printVersions
from timeit import default_timer as timer
import numpy as np
import webrtcvad

def load_model():
    SAMPLE_RATE = 16000
    BEAM_WIDTH = 500
    LM_ALPHA = 0.75
    LM_BETA = 1.85
    N_FEATURES = 26
    N_CONTEXT = 9
    alphabet = '/home/absin/Downloads/deepspeech-0.5.1-models/alphabet.txt'
    model = '/home/absin/Downloads/deepspeech-0.5.1-models/output_graph.pb'
    lm = '/home/absin/Downloads/deepspeech-0.5.1-models/lm.binary'
    trie = '/home/absin/Downloads/deepspeech-0.5.1-models/trie'
    print('Loading model from file {}'.format(model))
    model_load_start = timer()
    ds = Model(model, N_FEATURES, N_CONTEXT, alphabet, BEAM_WIDTH)
    model_load_end = timer() - model_load_start
    print('Loaded model in {:.3}s.'.format(model_load_end))
    print('Loading language model from files {} {}'.format(lm, trie))
    lm_load_start = timer()
    ds.enableDecoderWithLM(alphabet, lm, trie, LM_ALPHA, LM_BETA)
    lm_load_end = timer() - lm_load_start
    print('Loaded language model in {:.3}s.'.format(lm_load_end))
    stream_context = ds.setupStream()
    vad = webrtcvad.Vad()
    vad.set_mode(1)
    return ds, stream_context, vad

def detectPause(message, vad):
    return False
    time_m_sec = 30.0
    time_sec = time_m_sec/1000.0
    sameple_rate = 16000
    bit_depth = 2 #16bit
    chunk_size = time_sec*sameple_rate*bit_depth
    chunk_index = 0
    silence = 0
    max_silence = 30 #ms
    while((chunk_index+chunk_size)<=len(message)):
        frame = message[chunk_index:(chunk_index+int(chunk_size))]
        if(vad.is_speech(frame, sameple_rate)!=True):
            silence += time_m_sec
            print("Silence "+str(silence)+"ms")
            if(silence>max_silence):
                # 500 ms silence detected
                return True
        else:
            silence = 0
    return False


def finalSpeech(message, stream_context, ds):
    text = ds.finishStream(stream_context)
    stream_context = ds.setupStream()
    return "Final--->" + text

def tentativeSpeech(message, stream_context, ds):
    tentative_text = ds.intermediateDecode(stream_context)
    return "Tentative--->" + tentative_text

def performSpeechToText(message, stream_context, ds, vad):
    ds.feedAudioContent(stream_context, np.frombuffer(message, np.int16))
    if(detectPause(message, vad)):
        return finalSpeech(message, stream_context, ds)
    else:
        return tentativeSpeech(message, stream_context, ds)

ds = stream_context = vad = isSilence = None

async def hello(websocket, path):
    global ds, stream_context, vad, isSilence
    if(ds == None):
        ds, stream_context, vad = load_model()
        print('Primed')
        await websocket.send('Ready')
    else:
        print('Already primed')
        await websocket.send('Ready')
    async for message in websocket:
        print(len(message))
        if(len(message)>8000):
            sttt = performSpeechToText(message, stream_context, ds, vad)
            print(sttt)
            await websocket.send(sttt)

start_server = websockets.serve(hello, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
