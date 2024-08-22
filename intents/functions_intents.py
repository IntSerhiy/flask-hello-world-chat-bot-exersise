import uuid

import requests
from flask import Flask
from openai import OpenAI

from pinecone import Pinecone
CLIENT = OpenAI(api_key="sk-proj-mmRKHjeDcfL9vQxDezi4T3BlbkFJKXL7oAEiuxFsU8ZC9xVs")
pc = Pinecone(api_key="30f3efb4-4c57-40c4-bdfc-c2b6a4f52635")
index = pc.Index("intents")
app = Flask(__name__)

TOKEN = '7245262172:AAEnlFNAvSscBewXMeH10513YqtvmZZ39W8'

def add_intent_to_databases(name_intent, phrases):
    requests.post(
        "https://eu-central-1.aws.data.mongodb-api.com/app/data-ienxugs/endpoint/data/v1/action/insertOne",
        json={
            "collection": "Intents",
            "database": "Intent",
            "dataSource": "Cluster0",
            "document": {
                "name": name_intent,
                "phrases":phrases }
        },
        headers={'api-key': 'R5PeVST4qP0xcGmWYFmWlWC4m5Ofy4eD3IoHf7gk5SVAHPihj1hF1H1NB1M5nHqk'},
    )

    for phrase in phrases:
        embedding = get_embedding(phrase)
        save_embedding(embedding, phrase, name_intent)

def get_embedding(text: str):
    embedding = CLIENT.embeddings.create(input=text, model="text-embedding-3-small")
    return embedding.data[0].embedding

def save_embedding(embedding, phrase, intent_name):
    index.upsert(
        vectors = [
            {
                'id': str(uuid.uuid4()),
                'values': embedding,
                'metadata': {'phrase': phrase, 'intent_name':intent_name}
            }
        ]
    )