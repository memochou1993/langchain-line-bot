from flask import (
    abort,
    Flask,
    request,
    Response,
)
from dotenv import load_dotenv
from linebot.v3 import (
    WebhookHandler,
)
from linebot.v3.exceptions import (
    InvalidSignatureError,
)
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from explorers import (
    GoogleDriveExplorer,
)

import os
import logging

load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
webhook_handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

google_drive_inquiry_explorer = GoogleDriveExplorer()

@app.route('/', methods=['GET'])
def index():
    return Response('OK', status=200)

@app.route('/load', methods=['POST'])
def load():
    google_drive_inquiry_explorer.load()
    return Response(status=200)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info('Invalid signature. Please check your channel access token or channel secret.')
        abort(400)
    return Response(status=200)

@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    answer = google_drive_inquiry_explorer.ask(event.message.text)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=answer)],
            )
        )
