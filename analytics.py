import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, render_template
import json

app = Flask(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_ai_bot"]

def get_analytics_data():
    return {
        "total_users": db.users.count_documents({}),
        "total_messages": db.messages.count_documents({}),
        "total_files": db.files.count_documents({}),
        "total_websearches": db.websearch.count_documents({})
    }

@app.route('/')
def dashboard():
    data = get_analytics_data()
    return render_template('dashboard.html', data=data)

@app.route('/api/analytics')
def api_analytics():
    return json.dumps(get_analytics_data())

if __name__ == "__main__":
    app.run(debug=True)