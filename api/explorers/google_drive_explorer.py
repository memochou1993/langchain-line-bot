from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import GoogleDriveLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

import os

loader = GoogleDriveLoader(
    folder_id=os.environ['GOOGLE_DRIVE_FOLDER_ID'],
    service_account_key='credentials.json',
    recursive=False,
)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=4000,
    chunk_overlap=0,
    separators=[' ', ',', '\n'],
)
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo-16k')

class GoogleDriveExplorer:
    def __init__(self):
        self.load()

    def load(self) -> None:
        docs = loader.load()
        texts = text_splitter.split_documents(docs)
        db = Chroma.from_documents(texts, embeddings)
        retriever = db.as_retriever()
        self.qa = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

    def ask(self, question: str) -> str:
        return self.qa.run(question)
