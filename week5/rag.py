import os
import glob
from dotenv import load_dotenv
import gradio as gr

from langchain_community.document_loaders import DirectoryLoader,TextLoader
from langchain.text_splitter import CharacterTextSplitter
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings

db_name = "vector_db"

load_dotenv(override=True)

base_path = os.path.expanduser("~/projects/orcaai-configs/ship/prod")
folders = glob.glob(os.path.join(base_path, "*"))

def add_metadata(doc, doc_type):
    doc.metadata["doc_type"] = doc_type
    return doc

documents = []
for folder in folders:
    if not os.path.isdir(folder):
        continue  # skip files
    doc_type = os.path.basename(folder)
    loader = DirectoryLoader(
        folder,
        glob="**/*.json",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        recursive=True
    )
    folder_docs = loader.load()
    documents.extend([add_metadata(doc, doc_type) for doc in folder_docs])

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

print(f"Total number of chunks: {len(chunks)}")
print(f"Document types found: {set(doc.metadata['doc_type'] for doc in documents)}")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

if os.path.exists(db_name):
    Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
print(f"Vectorstore created with {vectorstore._collection.count()} documents")

collection = vectorstore._collection
count = collection.count()

sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
dimensions = len(sample_embedding)
print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")


llm = ChatOllama(model="llama3.2", temperature=0.7)

memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

retriever = vectorstore.as_retriever()

conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory)

def chat(question, history):
    result = conversation_chain.invoke({"question": question})
    return result["answer"]

view = gr.ChatInterface(chat, type="messages").launch(inbrowser=True)