import subprocess

with subprocess.Popen(
        ['python', 'update_audio_sample_recognizer_model.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True) as process:
    print(process.stdout.read())