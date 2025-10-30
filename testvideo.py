import cv2
import os
import time
import json
import re
import pandas as pd
from datetime import datetime
from celerytasks import *
from brevo_python import ApiClient, Configuration
from brevo_python.api.transactional_emails_api import TransactionalEmailsApi
from brevo_python.models.send_smtp_email import SendSmtpEmail

os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
os.environ['OPENCV_VIDEOIDO_DEBUG'] = '1'
class Camera:
    def __init__(self):
        self.video = cv2.VideoCapture(os.environ["CameraURL"], cv2.CAP_FFMPEG)
        self.oldtime = time.time()

        self.videowriter = cv2.VideoWriter.fourcc(*'VP80')
        self.width = int(self.video.get(3))
        self.height = int(self.video.get(4))

        # Determine starting index from existing files/results so we don't overwrite
        def _get_next_index():
            max_idx = 0
            try:
                files = os.listdir('static/livevideos')
                for f in files:
                    m = re.search(r'output(\d+)\.webm$', f)
                    if m:
                        idx = int(m.group(1))
                        if idx > max_idx:
                            max_idx = idx
            except Exception:
                pass

            try:
                with open('resultsfile.txt', 'r') as rf:
                    data = json.load(rf)
                    for k in data.keys():
                        m = re.search(r'output(\d+)\.webm$', k)
                        if m:
                            idx = int(m.group(1))
                            if idx > max_idx:
                                max_idx = idx
            except Exception:
                pass
            return max_idx + 1

        self.curvideosection = _get_next_index()
        self.videooutput = cv2.VideoWriter(f'static/livevideos/output{self.curvideosection}.webm', self.videowriter, 20, (self.width, self.height))
        self.videoresults = []
        self.videoresulttracker = -1

        self.videosegmentlength = 30

        # Track connection state so we start a new file when reconnecting
        self.connected = True
        self.videooutput_exists = True

        self.cfg = Configuration()
        self.cfg.api_key['api-key'] = os.environ.get("BREVO_API_KEY")
        self.lastemailsent = 0


    def __del__(self):
        self.video.release()

    def get_frame(self):
        if self.videoresulttracker != -1 and self.videoresulttracker < len(self.videoresults):
            if self.videoresults[self.videoresulttracker].ready():
                print(f"\nResults for segment #{self.videoresulttracker+1}:")
                result = self.videoresults[self.videoresulttracker].get(propagate=False)

                resultsfile = open("resultsfile.txt","r")
                videoresults = json.loads(resultsfile.read())
                resultsfile.close()

                resultsfile = open("resultsfile.txt","w")

                try:
                    print(result)
                    if "yes" in result.lower():
                        print(True)
                        # Use 1-based numbering to match file naming (output1.webm...)
                        videoresults[f"output{self.videoresulttracker+1}.webm"] = [True,""]

                        try:
                            if time.time()-self.lastemailsent <= 60:
                                print("It is too early to send an email.")
                            else:
                                print("PRETEND AN EMAIL IS SENT.")
                                # email = SendSmtpEmail(
                                #     sender={"name": "AI Camera", "email": "tahsanh12345@gmail.com"},
                                #     to=[{"email": "tahsanh12345@gmail.com", "name": "Tahsan"}],
                                #     subject="Suspicious Activity Detected",
                                #     html_content="<p>Dear user, <br>Suspicious activity has been detected. Go check it out.</p>"
                                # )

                                # api = TransactionalEmailsApi(ApiClient(self.cfg))
                                # resp = api.send_transac_email(email)
                                # self.lastemailsent = time.time()
                                # print(f"Email sent! messageId: {resp.message_id}")
                        except:
                            print("There was an error sending the email.")
                    elif "no" in result.lower():
                        print(False)
                        videoresults[f"output{self.videoresulttracker+1}.webm"] = [False,""]
                    else:
                        print(f"Custom result: {result}")
                        videoresults[f"output{self.videoresulttracker+1}.webm"] = ["Custom",result]
                except Exception as e:
                    print(f"Error processing result: {e}")
                    videoresults[f"output{self.videoresulttracker+1}.webm"] = ["Error",e]
                
                json_string = json.dumps(videoresults, indent=4)
                resultsfile.write(json_string)
                resultsfile.close()
                self.videoresulttracker+=1

        # Rotate segment if time elapsed (safely handle missing writer)
        if time.time() - self.oldtime >= self.videosegmentlength:
            try:
                if hasattr(self, 'videooutput') and self.videooutput is not None:
                    self.videooutput.release()
                    self.videoresults.append(upload_video.delay(self.curvideosection))
            except Exception:
                pass

            if self.videoresulttracker == -1:
                self.videoresulttracker += 1
            else:
                self.curvideosection += 1

            # Prepare a new writer (if camera currently connected we'll write to it on next frame)
            try:
                self.videooutput = cv2.VideoWriter(f'static/livevideos/output{self.curvideosection}.webm', self.videowriter, 20, (self.width, self.height))
                self.videooutput_exists = True
            except Exception:
                self.videooutput = None
                self.videooutput_exists = False

            self.oldtime = time.time()
            print("Rotated segment / prepared next output file")

        success, image = self.video.read()
        if not success:
            # On first failure, mark disconnected and close current writer so we start a new file when reconnecting
            if self.connected:
                print("Camera read failed — marking disconnected. Will start a new file on reconnect.")
                self.connected = False
                try:
                    if hasattr(self, 'videooutput') and self.videooutput is not None:
                        self.videooutput.release()
                except Exception:
                    pass

                # increment index so we start fresh next time
                self.curvideosection += 1
                self.videooutput = None
                self.videooutput_exists = False
            return None

        # If we've reconnected after a failure, create a new writer and continue (pretend nothing happened)
        if not self.connected:
            print("Camera reconnected — starting new file at next index")
            try:
                self.videooutput = cv2.VideoWriter(f'static/livevideos/output{self.curvideosection}.webm', self.videowriter, 20, (self.width, self.height))
                self.videooutput_exists = True
            except Exception as e:
                print(f"Failed to create video writer on reconnect: {e}")
                self.videooutput = None
                self.videooutput_exists = False
            self.connected = True
        
        greyimage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        currenttime = datetime.now()
        currenttime = currenttime.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(greyimage, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 6)
        cv2.putText(greyimage, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)

        if hasattr(self, 'videooutput') and self.videooutput is not None:
            try:
                self.videooutput.write(image)
            except Exception as e:
                print(f"Error writing frame to videooutput: {e}")
        else:
            # No writer available — skip writing but continue streaming
            pass

        ret, jpeg = cv2.imencode('.jpg', greyimage)
        return jpeg.tobytes()