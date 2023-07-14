from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import GoogleDriveLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

import os

load_dotenv()

app = Flask(__name__)

loader = GoogleDriveLoader(
    folder_id=os.environ['GOOGLE_DRIVE_FOLDER_ID'],
    credentials_path='credentials.json',
    token_path='token.json',
    recursive=False,
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=4000,
    chunk_overlap=0,
    separators=[' ', ',', '\n'],
)

texts = text_splitter.split_documents(docs)
embeddings = OpenAIEmbeddings()
db = Chroma.from_documents(texts, embeddings)
retriever = db.as_retriever()

llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')
qa = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
webhook_handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route('/', methods=['GET'])
def index():
    return 'OK'

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info('Invalid signature. Please check your channel access token or channel secret.')
        abort(400)
    return 'OK'

@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    answer = qa.run(event.message.text)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=answer)],
            )
        )
