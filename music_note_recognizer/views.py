import numpy as np
from scipy.io.wavfile import write
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def index(request):
    if request.method == "POST":
        audio = np.frombuffer(request.body, dtype=np.int8)
        
        print(audio[:10], audio.shape)
        # data = np.random.uniform(-1,1,44100) # 44100 random samples between -1 and 1
        # scaled = np.int16(data/np.max(np.abs(data)) * 32767)
        write('test.wav', 44100, audio)

    return render(request, 'index.html')
