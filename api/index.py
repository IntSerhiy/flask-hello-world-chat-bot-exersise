import uuid

from flask import Flask, request, jsonify
import requests
from openai import OpenAI
from pinecone import Pinecone

from intents.functions_intents import add_intent_to_databases

CLIENT = OpenAI(api_key="sk-proj-mmRKHjeDcfL9vQxDezi4T3BlbkFJKXL7oAEiuxFsU8ZC9xVs")
pc = Pinecone(api_key="30f3efb4-4c57-40c4-bdfc-c2b6a4f52635")
index = pc.Index("intents")
app = Flask(__name__)

TOKEN = '7245262172:AAEnlFNAvSscBewXMeH10513YqtvmZZ39W8'

@app.route('/intent', methods=['POST'])
def intent():
    content = request.get_json()
    name_intent = content['name']
    phrases = content['phrases']
    add_intent_to_databases(name_intent, phrases)
    return 'ok'

@app.route('/')
def hello():
    return 'hello'


@app.route('/intent', methods=['GET'])
def get_intent():
    response = requests.post(
    "https://eu-central-1.aws.data.mongodb-api.com/app/data-ienxugs/endpoint/data/v1/action/find",
    json={
        "collection": "Intents",
        "database": "Intent",
        "dataSource": "Cluster0"},
        headers={'api-key': 'R5PeVST4qP0xcGmWYFmWlWC4m5Ofy4eD3IoHf7gk5SVAHPihj1hF1H1NB1M5nHqk'},
    )

    print(response.json()['documents'])

@app.route('/delete_intent', methods=['POST'])
def delete_intent():
    # Отримання даних із запиту
    data = request.get_json()
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
                "_id": {"$oid": document_id}  # Переконайтеся, що document_id — це рядок
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
                return jsonify({"error": "Exception occurred while deleting vector from Pinecone", "details": str(e)}), 500
        else:
            return jsonify({"error": "No document matched the provided _id in MongoDB"}), 404
    else:
        return jsonify({"error": "Failed to delete document from MongoDB", "details": mongo_response.json()}), mongo_response.status_code
