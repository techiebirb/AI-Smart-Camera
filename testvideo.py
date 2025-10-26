import cv2
import os
import time
import json
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
        self.videooutput = cv2.VideoWriter('static/livevideos/output1.webm', self.videowriter, 20, (self.width, self.height))
        self.curvideosection = 1
        self.videoresults = []
        self.videoresulttracker = -1

        self.videosegmentlength = 30

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
                        videoresults[f"output{self.videoresulttracker}.webm"] = [True,""]

                        try:
                            if time.time()-self.lastemailsent <= 60:
                                print("It is too early to send an email.")
                            else:
                                email = SendSmtpEmail(
                                    sender={"name": "AI Camera", "email": "tahsanh12345@gmail.com"},
                                    to=[{"email": "tahsanh12345@gmail.com", "name": "Tahsan"}],
                                    subject="Suspicious Activity Detected",
                                    html_content="<p>Dear user, <br>Suspicious activity has been detected. Go check it out.</p>"
                                )

                                api = TransactionalEmailsApi(ApiClient(self.cfg))
                                resp = api.send_transac_email(email)
                                self.lastemailsent = time.time()
                                print(f"Email sent! messageId: {resp.message_id}")
                        except:
                            print("There was an error sending the email.")
                    elif "no" in result.lower():
                        print(False)
                        videoresults[f"output{self.videoresulttracker}.webm"] = [False,""]
                    else:
                        print(f"Custom result: {result}")
                        videoresults[f"output{self.videoresulttracker}.webm"] = ["Custom",result]
                except Exception as e:
                    print(f"Error processing result: {e}")
                    videoresults[f"output{self.videoresulttracker}.webm"] = ["Error",e]
                
                json_string = json.dumps(videoresults, indent=4)
                resultsfile.write(json_string)
                resultsfile.close()
                self.videoresulttracker+=1

        if time.time()-self.videosegmentlength >= self.oldtime:
            self.videooutput.release()
            self.videoresults.append(upload_video.delay(self.curvideosection))
            if self.videoresulttracker == -1:
                self.videoresulttracker+=1
            else:
                self.curvideosection+=1

            self.videooutput = cv2.VideoWriter(f'static/livevideos/output{self.curvideosection}.webm', self.videowriter, 20, (self.width, self.height))
            self.oldtime = time.time()
            print("Hello")

        success, image = self.video.read()
        if not success:
            return None
        
        greyimage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        currenttime = datetime.now()
        currenttime = currenttime.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(greyimage, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 6)
        cv2.putText(greyimage, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)

        self.videooutput.write(image)

        ret, jpeg = cv2.imencode('.jpg', greyimage)
        return jpeg.tobytes()