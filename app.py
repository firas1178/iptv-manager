from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import requests
import traceback

app = Flask(__name__, static_folder='static')
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.json
        image_b64 = data.get('image')
        media_type = data.get('media_type', 'image/jpeg')

        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 150,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': image_b64}},
                        {'type': 'text', 'text': 'Extract TV MAC and Device Key from this image. Reply ONLY as JSON: {"mac":"xx:xx:xx:xx:xx:xx","key":"xxxxxx"}'}
                    ]
                }]
            },
            timeout=30
        )
        result = response.json()
        text = result['content'][0]['text'].replace('```json','').replace('```','').strip()
        parsed = json.loads(text)
        return jsonify(parsed)
    except Exception as e:
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e)}), 500

@app.route('/queue', methods=['POST'])
def queue_job():
    try:
        data = request.json
        name = data.get('name')
        mobile = data.get('mobile')
        mac = data.get('mac')
        key = data.get('key')

        jobs_file = 'jobs.json'
        jobs = []
        if os.path.exists(jobs_file):
            with open(jobs_file, 'r') as f:
                jobs = json.load(f)

        jobs.append({'name': name, 'mobile': mobile, 'mac': mac, 'key': key, 'status': 'pending'})

        with open(jobs_file, 'w') as f:
            json.dump(jobs, f)

        return jsonify({'status': 'queued', 'total': len(jobs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['GET'])
def get_jobs():
    jobs_file = 'jobs.json'
    if os.path.exists(jobs_file):
        with open(jobs_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/jobs/clear', methods=['POST'])
def clear_jobs():
    if os.path.exists('jobs.json'):
        os.remove('jobs.json')
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
