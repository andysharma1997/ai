$(document).ready(function(){
  defineVariables();
  checkMicrophone();
});


function initWebsocket(audioStream) {
	window.context = new AudioContext({
    sampleRate: 16000,
  });
	window.micStream = audioStream;
	window.scriptNode = window.context.createScriptProcessor(4096, 1, 1);
	window.scriptNode.addEventListener('audioprocess', function (e) {
		var floatSamples = e.inputBuffer.getChannelData(0);
    console.log('Sending');
		window.socket.send(Int16Array.from(floatSamples.map(function (n) {
			return n * window.MAX_INT;
		})));
	});
	window.context.addEventListener('statechange', toggleWebsocket);
}

function toggleWebsocket(e) {
	var context = e.target;
	if (context.state === 'running') {
		newWebsocket();
	} else if (context.state === 'suspended') {
		closeWebsocket();
	}
}


function newWebsocket(speaker) {
	try{
		closeWebsocket(speaker);
	} catch (e) {
		console.log(e);
	}
	var websocketPromise = new Promise(function (resolve, reject) {
		var socket = new WebSocket('ws://localhost:8765/');
		socket.addEventListener('open', resolve);
		socket.addEventListener('error', reject);
	});
	Promise.all([websocketPromise]).then(function (values) {
		window.socket = values[0].target;
		if(!window.transcriptonEventsReg){
			window.socket.addEventListener('close', function (e) {
				console.trace('Websocket closing..');
			});
			window.socket.addEventListener('error', function (e) {
				console.trace('Error from websocket', e);
			});
			window.socket.addEventListener('message', function (e) {
        console.log("----------------"+e.data);
				if (e.data == 'Ready')
					startByteStream(e);
				else if (e.data == 'Stop')
					stopByteStream();
			}, { once: true });
      window.socket.addEventListener('message',
        function(e) {
          console.log("----------------"+e.data);
          if(e.data.includes('Tentative--->')){
            $("#tentative").html(e.data);
          } else{
            var html = "<li>"+e.data+"</li>";
            $("#transcription").append(html);
          }
        });
		}
	}).catch(console.log.bind(console));
}

function closeWebsocket() {
	stopByteStream();
	if (window.socket && window.socket.readyState === window.socket.OPEN)
		window.socket.close();
}

function startByteStream(e) {
	console.trace('Starting stream')
	window.sourceNode = window.context.createMediaStreamSource(window.micStream);
	window.sourceNode.connect(window.scriptNode);
	window.scriptNode.connect(window.context.destination);
}
function stopByteStream() {
	console.trace('Stopping stream');
	if (window.sourceNode)
		window.sourceNode.disconnect();
}

defineVariables = function(){
  window.isMicActive = false;
  window.isAudioJackListener = false;
  window.context;
  window.socket;
  window.micStream;
  window.scriptNode;
  window.sourceNode;
  window.transcriptonEventsReg = false;
  window.MAX_INT = Math.pow(2, 16 - 1) - 1;
}

checkMicrophone = function(){
  updateDeviceList();
	navigator.mediaDevices.ondevicechange = function (event) {
		updateDeviceList();
	}
  setTimeout(function () {
		if (!window.isAudioJackListener) {
			var audioJackListener = setInterval(function () {
				navigator.mediaDevices.enumerateDevices();
				if (window.isAudioJackListener) {
					clearInterval(audioJackListener);
				}
			}, 20);
		}
	}, 3000);
}

updateDeviceList = function () {
	navigator.mediaDevices.getUserMedia({ audio: true })
		.then(function (stream) {
			isAudioJackListener = true;
		}).catch(function (err) {
			alert(' Your device does not have an active microphone!', 1);
			$('.transcribe').attr("disabled", "disabled");
		});
}

start = function(){
  navigator.mediaDevices.getUserMedia({ audio: true })
		.then(function (stream) {
			initWebsocket(stream);
		}).catch(function (err) {
			alert(' Your device does not have an active microphone!', 1);
			$('.transcribe').attr("disabled", "disabled");
		});
}
