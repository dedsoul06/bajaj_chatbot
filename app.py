from flask import Flask, request, jsonify, send_from_directory
from chatbot import LocalBajajChatbot
import threading
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize chatbot
bot = LocalBajajChatbot()

# Load data in background
def init_bot():
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    bot.load_data(
        pdf_folder=os.path.join(data_path, 'quarterly_reports'),
        csv_path=os.path.join(data_path, 'financials.csv')
    )
threading.Thread(target=init_bot).start()

# API Endpoint
@app.route('/api/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    if not question:
        return jsonify({"error": "Missing 'question'"}), 400
    
    try:
        answer = bot.answer_question(question)
        return jsonify({
            "answer": answer,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# Serve Frontend
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create required folders if they don't exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('data/quarterly_reports', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
