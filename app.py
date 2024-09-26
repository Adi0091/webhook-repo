from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timezone
from flask import render_template
app = Flask(__name__)

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client['webhook_db']
collection = db['github_events']

@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find({}, {'_id': 0}).sort('timestamp', -1))
    return jsonify(events)

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json

        event_type = request.headers.get('X-GitHub-Event')
        timestamp = datetime.now(timezone.utc)

        event_data = {}  # Initialize event data

        # Parse Push Event
        if event_type == 'push':
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]
            event_data = {
                "event": "push",
                "author": author,
                "to_branch": to_branch,
                "timestamp": timestamp
            }

        # Parse Pull Request Event
        elif event_type == 'pull_request':
            author = data['pull_request']['user']['login']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            event_data = {
                "event": "pull_request",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }

        # Parse Merge Event (Optional)
        elif event_type == 'pull_request' and data['pull_request']['merged']:
            author = data['pull_request']['user']['login']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            event_data = {
                "event": "merge",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }

        # Insert into MongoDB
        collection.insert_one(event_data)
        return jsonify({"message": "Event received and stored!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
