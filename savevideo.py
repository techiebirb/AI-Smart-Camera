import cv2
import time
from datetime import datetime
from celerytasks import *

# videosource = "crimedetectionproject/samplevideos/policecars.mp4"
videosource = "crimedetectionproject/samplevideos/crime.mp4"
# videosource = "crimedetectionproject/samplevideos/policetape.mp4"

# videosource = "crimedetectionproject/samplevideos/shopping.mp4"
# videosource = "crimedetectionproject/samplevideos/grocerystore.mp4"
# videosource = "crimedetectionproject/samplevideos/mall.mp4"

# videosource = 0

video = cv2.VideoCapture(videosource)
videowriter = cv2.VideoWriter_fourcc(*'mp4v')
width = int(video.get(3))
height = int(video.get(4))
videooutput = cv2.VideoWriter('crimedetectionproject/livevideos/output1.mp4', videowriter, 20, (width, height))
curvideosection = 1
oldtime = time.time()
videoresults = []
videoresulttracker = -1

videosegmentlength = 5
numbervideosegments = 100000



while True:
    if videoresulttracker != -1 and videoresulttracker < len(videoresults):
        if videoresults[videoresulttracker].ready():
            print(f"Results for segment #{videoresulttracker+1}:")
            result = videoresults[videoresulttracker].get(propagate=False)
            try:
                if "yes" in result.lower():
                    print(True)
                elif "no" in result.lower():
                    print(False)
                else:
                    print(f"Custom result: {result}")
            except Exception as e:
                print(f"Error processing result: {e}")
            videoresulttracker+=1
    check,frame = video.read()
    if check:
        currenttime = datetime.now()
        currenttime = currenttime.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 6)
        cv2.putText(frame, currenttime, (25, 25), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
        cv2.imshow("Tahsan",frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    videooutput.write(frame)
    if time.time()-oldtime >= videosegmentlength:
        videooutput.release()
        videoresults.append(upload_video.delay(curvideosection))
        if videoresulttracker == -1:
            videoresulttracker+=1

        if curvideosection+1 >= numbervideosegments+1:
            break
        else:
            curvideosection+=1
        videooutput = cv2.VideoWriter(f'crimedetectionproject/livevideos/output{curvideosection}.mp4', videowriter, 20, (width, height))
        oldtime = time.time()


video.release()
videooutput.release()
cv2.destroyAllWindows()

for i in videoresults[videoresulttracker:]:
    while not i.ready():
        pass
    print(f"Results for segment #{videoresulttracker+1}:")
    result = videoresults[videoresulttracker].get(propagate=False)
    if "yes" in result.lower():
        print(True)
    elif "no" in result.lower():
        print(False)
    else:
        print(f"Custom result: {result}")
