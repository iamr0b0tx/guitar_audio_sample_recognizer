    /**
 * Allows recording via the devices microphone.
 */

class Recorder
{
    /**
     * Constraints setup for mono.
     * Currently now to modify them.
     * It should be noted that these settings are ignored on most
     * systems and we get stereo at a 44K sampleRate regardless of these settings.
     */
    static  _constraints = {
              audio: 
                  {
                        channelCount: 1,
                        mimeType: 'audio/wav',
                        sampleRate: 8192,
                        sampleSize: 8,
                        autoGainControl: true,
                        noiseSuppression: true,
                        echoCancellation: true,
                  }
            };

    constructor(desiredChannels)
    {
        this._desiredChannels = desiredChannels;
        this._reset();
    }


    /*
     * Start recording.
     * 
     * errorCallback(e) - a function  that is called if the start fails.
     * 
     */
    start(errorCallback)
    {
        this._reset();
        this._context = new AudioContext();

        // request permission and if given
        // wire our audio control to the media stream.  
        navigator
            .mediaDevices
            .getUserMedia(Recorder._constraints)
            .then((stream) => this._wireRecordingStream(stream))
            .catch(e => errorCallback(e));

        // TODO: consider giving the user the ability to select an input device.
    }

    /*
     * Stops a currently active recording.
     */
    stop()
    {
        if (this._context != null)
        {
            this._context.close();
            this._context = null;
        }
    }

    /**
     * check if the user's phone supports media api
     */
    hasGetUserMedia() 
    {
          return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    /**
     * returns a Blob containing a wav file of the recording.  
     */
    getWav()
    {
        if (this._mergedChannelData == null)
            this._mergeChannels();

        let wav = new Wav(this._mergedChannelData, this._actualChannelCount, this._actualSampleRate);

        return wav.getBlob();
    }


    /**
     * resets the Recorder so we can restart the recording.
     */
    _reset()
    {
        this._channels = null;
        this._actualChannelCount = -1;

        // this will be updated when the recording starts to the actual rate.
        this._actualSampleRate = -1;

        // after _mergeChannels is called this will contain
        // a single float32 array of the underlying channel 
        // data interleaved to create a single audio stream.
        this._mergedChannelData = null;

    }


    _initChannelBuffers(actualChannels) 
    {
        if (this._channels == null)
        {
            this._channels = [];
            this._actualChannelCount = actualChannels;

            for (var i = 0; i < actualChannels; i++) 
            {
                this._channels.push(new Channel());
            }
        }
    }


    /**
     * The start() method uses this method to initialise the media stream
     * and wire up the 'onaudioprocess'or to capture the recording.
     */
    _wireRecordingStream(stream)
    {
        // https://developers.google.com/web/fundamentals/media/recording-audio/

        // Setup recording.
        this._source = this._context.createMediaStreamSource(stream);

        this._node = (this._context.createScriptProcessor || this._context.createJavaScriptNode)
            .call(this._context, 4096, this._desiredChannels, this._desiredChannels); // 4K buffer and we prefer a single (mono) channel.

        // the context may have ignored our preferred sample rate.
        this._actualSampleRate = this._context.sampleRate;

        this._node.onaudioprocess = (e) => this._storeAudio(e.inputBuffer);

        this._source.connect(this._node);
        this._node.connect(this._context.destination);
    }

    /**
     * This is the callback for 'onaudioprocess' where we store the recorded data 
     * to each channel buffer.
     */
    _storeAudio(inputBuffer) 
    {
        this._initChannelBuffers(inputBuffer.numberOfChannels);

        for (var i = 0; i < this._actualChannelCount; i++) 
        {
            this._channels[i].storeAudioPacket(inputBuffer.getChannelData(i));
        }
    }

    // Merges all channels into a single float32Array.
    // Channels are merged by interleaving data packet from each channel into a single stream.
    _mergeChannels() 
    {
        if (this._actualChannelCount === 2) 
        {
            this._mergedChannelData = this._interleave(this._channels[0], this._channels[1]);
        } 
        else 
        {
            this._mergedChannelData = this._channels[0].getAudioData();
        }
    }

    /**
     ** interleaves two channel buffers into a single float32 array.
     */
    _interleave(lhsChannel, rhsChannel) 
    {
        let length = lhsChannel.getLength() + rhsChannel.getLength();
        let result = new Float32Array(length);

        let index = 0;
        let inputIndex = 0;this._channels 

        let lhsData = lhsChannel.getAudioData();
        let rhsData = rhsChannel.getAudioData();

        while (index < length) 
        {
            result[index++] = lhsData[inputIndex];
            result[index++] = rhsData[inputIndex];
            inputIndex++;
        }
        return result;
    }
}

/**
 * Used to buffer audio data for a single channel.
 */
class Channel
{
    constructor()
    {
        /** 
         * the total no of Float32's stored in all of the audio packets.
         */
        this._length = 0;

        // an array of audio packets (Float32Array) captured as the recording progresses.
        // 
        this._audioPackets = [];

        // If flatten has been called this will be a Float32Array
        // contain all of the combined audio packets as  a single array.
        this._flattened = null;
    }

    getLength()
    {
        return this._length;
    }

    /**
     * returns a single audio packet stored at the given index.
     */
    getAudioPacket(index)
    {
        return this._audioPackets[index];
    }

    /**
     * returns the entire underlying data (Float32s) as a single Float32 array
     * If it hasn't already been done this method will call flatten to
     * combine all of the packets into a singl data array.
     */
    getAudioData()
    {
        if (this._flattened == null)
            this._flatten();

        return this._flattened;
    }

    // Stores an audioPacket (Float32Array) to _audioPackets
    storeAudioPacket(audioPacket)
    {
        this._audioPackets.push(new Float32Array(audioPacket));
        this._length += audioPacket.length;
    }

    /**
     * coalesce all of the _audioPackets into a single float32Array
     */
    _flatten() 
    {
        this._flattened = new Float32Array(this._length);
        let  offset = 0;
        for (let i = 0; i < this._audioPackets.length; i++) 
        {
            this._flattened.set(this._audioPackets[i], offset);
            offset += this._audioPackets[i].length;
        }
    }
}

/**
 * The logic for creating a wav file (well just the data structure actually) from
 * a stream of audioData
 * 
 * audioData - Float32Array containing the interleaved data from all channels.
 * channelCount - the number of channels interleaved into the audioData
 * sampleRate - the sampleRate of the audioData.
 */
class Wav
{
    /**
     * expects a single float32array from which it will create a wav file.
     */
    constructor(audioData, channelCount, sampleRate)
    {
        this._audioData = audioData;
        this._channelCount = channelCount;
        this._sampleRate = sampleRate;
    }

    /**
     * returns the wav file as a blob.
     */
    getBlob()
    {
        let wav = this._encodeAsWAV();
        let audioBlob = new Blob([wav], { type: "audio/wav" });

        return audioBlob;
    }

    /**
     * Encodes _audioData into a wav file by adding the 
     * standard wav header.
     */
    _encodeAsWAV() 
    {
        let audioData = this._audioData;

        var wavBuffer = new ArrayBuffer(44 + audioData.length * 2);
        var view = new DataView(wavBuffer);

        /* RIFF identifier */
        this._writeString(view, 0, 'RIFF');
        /* RIFF chunk length */
        view.setUint32(4, 36 + audioData.length * 2, true);
        /* RIFF type */
        this._writeString(view, 8, 'WAVE');
        /* format chunk identifier */
        this._writeString(view, 12, 'fmt ');
        /* format chunk length */
        view.setUint32(16, 16, true);
        /* sample format (raw) */
        view.setUint16(20, 1, true);
        /* channel count */
        view.setUint16(22, this._channelCount, true);
        /* sample rate */
        view.setUint32(24, this._sampleRate, true);
        /* byte rate (sample rate * block align) */
        view.setUint32(28, this._sampleRate * 4, true);
        /* block align (channel count * bytes per sample) */
        view.setUint16(32, this._channelCount * 2, true);
        /* bits per sample */
        view.setUint16(34, 16, true);
        /* data chunk identifier */
        this._writeString(view, 36, 'data');
        /* data chunk length */
        view.setUint32(40, audioData.length * 2, true);

        this._floatTo16BitPCM(view, 44, audioData);

        return view;
    }

    _floatTo16BitPCM(output, offset, input) 
    {
        for (var i = 0; i < input.length; i++, offset += 2) 
        {
            var s = Math.max(-1, Math.min(1, input[i]));
            output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
    }

    _writeString(view, offset, string) 
    {
        for (var i = 0; i < string.length; i++) 
        {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
}