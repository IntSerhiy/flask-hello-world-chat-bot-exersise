import uuid

from flask import Flask, request
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
