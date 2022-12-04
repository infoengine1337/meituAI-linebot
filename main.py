from flask import Flask
from flask import request
import os
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, ImageMessage, TextSendMessage, ImageSendMessage)
import base64
import requests
import json

# generate instance
app = Flask(__name__)

# get environmental value from heroku
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
FREEIMAGE_API = os.environ["FREEIMAGE_API"]
line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# endpoint
@app.route("/")
def test():
    return "<h1>It Works!</h1>"

# endpoint from linebot
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# handle message from LINE
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="画像を送信するにょ"))

# handle Image message from LINE
@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):

    AIBeauty_url = "https://openapi.mtlab.meitu.com/v1/stable_diffusion_anime?api_key=237d6363213c4751ba1775aba648517d&api_secret=b7b1c5865a83461ea5865da3ecc7c03d"

    image_co = line_bot_api.get_message_content(event.message.id)

    image_b64_before = b""
    for chunk in image_co.iter_content():
        image_b64_before += chunk
    
    ss = json.dumps(
        {
            "parameter": {
                "rsp_media_type": "jpg",
            },
            "extra": {},
            "media_info_list": [{
                "media_data": base64.b64encode(image_b64_before).decode('utf-8'),
                "media_profiles": {
                    "media_data_type":"jpg"
                },
                "media_extra": {
                }
            }]

        }
    )

    resp2 = requests.post(AIBeauty_url, data=ss)
    image_b64_after = base64.b64decode(resp2.json()["media_info_list"][0]["media_data"])

    params = {
        "key": FREEIMAGE_API,
        "source": base64.b64encode(image_b64_after)
    }

    resp1 = requests.post("https://freeimage.host/api/1/upload", data=params).json()

    print(resp1)
    main_url = resp1["image"]["url"]
    thumb_url = resp1["image"]["thumb"]["url"]

    image_message = ImageSendMessage(
        original_content_url=main_url,
        preview_image_url=thumb_url,
    )

    line_bot_api.reply_message(
        event.reply_token,
        image_message
    )

if __name__ == "__main__":
	app.run()