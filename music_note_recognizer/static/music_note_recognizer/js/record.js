//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

// audio previewer
var au = document.getElementById("audio");
var result = document.getElementById("result");

// the csrf token
var form = document.getElementById("form");


function startRecording() {
	console.log("recording...");

	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    
    var constraints = { audio: true, video:false }


	/*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device

		*/
		audioContext = new AudioContext();

		//update the format 
		document.getElementById("formats").innerHTML="Format: 1 channel pcm @ "+audioContext.sampleRate/1000+"kHz"

		/*  assign to gumStream for later use  */
		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input, {numChannels:1})

		//start the recording process
		rec.record()

		console.log("Recording started");

	}).catch(function(err) {
	  	//if getUserMedia() fails
		console.log("error occured while starting recording!")
		console.log(err)
	});
}

function stopRecording() {
	console.log("stop recording");
	
	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {	
	result.innerText = "Analysing..."
	var url = URL.createObjectURL(blob);

	//name of .wav file to use during upload and download (without extendion)
	var filename = new Date().toISOString();

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	// upload to server
	var xhr=new XMLHttpRequest();
	xhr.onload = function(e) {
		if(this.readyState === 4) {
			console.log(e.target.responseText)
			response = JSON.parse(e.target.responseText)
			
			console.log("Server returned: ");
			if(response.result){
				result.innerText = "Very Good!"

			}else{
				result.innerText = "Not Very Good!"
			}
		}
	};
	var fd = new FormData(form);
	fd.append("audio_data", blob, filename);
	xhr.open("POST","./predict", true);
	xhr.send(fd);
}

function animate_btn(element) {
	result.innerText = "Get Ready..."
	element.className = 'note animate-class';

	setTimeout(async () => {
		startRecording();
		result.innerText = "Recording...Play Now!"

		const sleep = m => new Promise(r => setTimeout(r, m));
		await sleep(3000);

		stopRecording();
		element.className = 'note';

	}, 3000);
}
