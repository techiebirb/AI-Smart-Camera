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

cfg = Configuration()
cfg.api_key['api-key'] = os.environ.get("BREVO_API_KEY")
lastemailsent = 0

@app.task
def upload_video(curvideosection):
    try:
        print("TEST")
        videofileai = client.files.upload(file=f"livevideos/output{curvideosection}.mp4")
        while videofileai.state.name == 'PROCESSING':
            videofileai = client.files.get(name=videofileai.name)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                videofileai,
                "Is there any crime or suspicous activity that appears in this video? Just tell me a simple yes or no. If you see a black screen or are unable to tell, just say no."
                # "If there is a waterbottle, just say Yes. If not, say No. The answer should not contain anything besides a Yes or No.",
                # "If there is any movement of vehicles, then just say Yes. Otherwise, just say No."
            ],
        )
        return response.text
    except Exception as e:
        return "THERE WAS AN ERROR. COULD NOT RUN." + e

# @app.task
# def send_email(curvideosection):
#     try:
#         if time.time()-lastemailsent <= 60:
#             return "It is too early to send an email."
#         email = SendSmtpEmail(
#             sender={"name": "AI Camera", "email": "tahsanh12345@gmail.com"},
#             to=[{"email": "tahsanh12345@gmail.com", "name": "Tahsan"}],
#             subject="Suspicious Activity Detected",
#             html_content="<p>Dear user, <br>Suspicious activity has been detected. Go check it out.</p>"
#         )

#         api = TransactionalEmailsApi(ApiClient(cfg))
#         resp = api.send_transac_email(email)
#         lastemailsent = time.time()
#         return f"Email sent! messageId: {resp.message_id}"
#     except:
#         return "There was an error sending the email."