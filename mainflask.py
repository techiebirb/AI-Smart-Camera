from flask import Flask, render_template, Response, request
from testvideo import Camera
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import json
import os
import shutil

app_path = os.path.join(os.path.dirname(__file__), '.')
dotenv_path = os.path.join(app_path, '.env')
load_dotenv(dotenv_path)

# RESETTING STUFF
shutil.rmtree("static/livevideos")
os.makedirs("static/livevideos")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Mark as not suspicous/suspicous button
# Schedule auto delete
# Manual delte video
# video auto continuing

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history/')
def history():
    videols = os.listdir("static/livevideos")
    # print(videols)
    videostatuses = {}
    resultsfile = open("resultsfile.txt","r")
    videostatuses = json.loads(resultsfile.read())
    print(videostatuses)
    resultsfile.close()
    return render_template("history.html", videols=videols, videostatuses=videostatuses)


@app.route('/videoplayer')
def videoplayer():
    videoid = request.args["videoid"]
    print(videoid)
    return render_template("videoplayer.html", videoid=videoid)
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")