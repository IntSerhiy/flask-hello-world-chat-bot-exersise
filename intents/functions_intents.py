import uuid

import requests
from flask import Flask, jsonify
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

def delete_vector(data):
    data = data
    print(f"Received data: {data}")
    document_id = data.get('_id')
    vector_id = data.get('vector_id')

    if not document_id or not vector_id:
        return jsonify({"error": "No '_id' or 'vector_id' provided"}), 400

    mongo_response = requests.post(
        "https://eu-central-1.aws.data.mongodb-api.com/app/data-ienxugs/endpoint/data/v1/action/deleteOne",
        json={
            "dataSource": "Cluster0",
            "database": "Intent",
            "collection": "Intents",
            "filter": {
                "_id": {"$oid": document_id}
            }
        },
        headers={
            'api-key': 'R5PeVST4qP0xcGmWYFmWlWC4m5Ofy4eD3IoHf7gk5SVAHPihj1hF1H1NB1M5nHqk',
            'Content-Type': 'application/json'
        }
    )
    if mongo_response.status_code == 200:
        mongo_result = mongo_response.json()
        if mongo_result.get('deletedCount', 0) > 0:
            try:
                pinecone_response = index.delete(ids=[vector_id])
                if pinecone_response:
                    return jsonify({"message": "Document and vector deleted successfully"}), 200
                else:
                    return jsonify({"error": "Failed to delete vector from Pinecone"}), 500
            except Exception as e:
                return jsonify(
                    {"error": "Exception occurred while deleting vector from Pinecone", "details": str(e)}), 500
        else:
            return jsonify({"error": "No document matched the provided _id in MongoDB"}), 404
    else:
        return jsonify({"error": "Failed to delete document from MongoDB",
                        "details": mongo_response.json()}), mongo_response.status_code



def search(query: str, top_k):
    embedding = get_embedding(query)
    result = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    return list(map(lambda x: {"intent_name":x.metadata['intent_name'], "phrase": x.metadata['phrase']}, result.matches))

def promt(query):
    intents = search(query, 10)

    if not intents:
        return jsonify({"error": "No intents found for the given query."}), 404

    examples = []
    for i, intent in enumerate(intents, 1):
        example = f"""
            {i}.  - Фраза: "{intent['phrase']}"
            Назва інтенту: {intent['intent_name']}
              
            """
        examples.append(example.strip())

    prompt = f"""
       Ви є асистентом, який обирає найбільш підходящий інтент і фрази, обери фразу яку ти повернеш.

    Фрази:
    {'\n'.join(examples)}

    - Фраза: "{query}"
    Назва інтенту:  
        """


    return prompt


def call_gpt(prompt, model="gpt-3.5-turbo"):
    try:
        response = CLIENT.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
            ],
        )
        message = response.choices[0].message.content
        return message.strip()
    except Exception as e:
        return str(e)


def generetive_prompt(phrase):
    prompt = promt(phrase)
    intent = call_gpt(prompt)
    return intent
