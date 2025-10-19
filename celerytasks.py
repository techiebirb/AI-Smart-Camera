# celery -A celerytasks worker --pool=solo -l info
# celery -A celerytasks purge

from celery import Celery
from google import genai
from brevo_python import Configuration

from dotenv import load_dotenv
import os

app_path = os.path.join(os.path.dirname(__file__), '.')
dotenv_path = os.path.join(app_path, '.env')
load_dotenv(dotenv_path)

app = Celery('tasks', backend='rpc://', broker='amqp://guest@localhost//', accept_content=['json'])

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
lastemailsent = 0

@app.task
def upload_video(curvideosection):
    video_filename = f"output{curvideosection}.webm"
    try:
        print("TEST")
        print("Test2")
        videofileai = client.files.upload(file=f"static/livevideos/{video_filename}")
        while videofileai.state.name == 'PROCESSING':
            videofileai = client.files.get(name=videofileai.name)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                videofileai,
                "Is there any crime or suspicous activity that appears in this video? Just tell me a simple yes or no. If you see a black screen or are unable to tell, just say no."
            ],
        )

        return response.text
    except Exception as e:
        return f"THERE WAS AN ERROR. COULD NOT RUN. {e}"

