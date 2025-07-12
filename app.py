from flask import Flask, request, jsonify
from chatbot import LocalBajajChatbot  # Import your existing class
import threading

app = Flask(__name__)

# Initialize chatbot
bot = LocalBajajChatbot()

# Load data in background
def init_bot():
    bot.load_data("data/quarterly_reports", "data/financials.csv")
threading.Thread(target=init_bot).start()

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    if not question:
        return jsonify({"error": "Missing 'question'"}), 400
    
    try:
        answer = bot.answer_question(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return """
    <h1>Bajaj Chatbot</h1>
    <form onsubmit="ask(); return false;">
        <input id="question" placeholder="Ask something...">
        <button>Submit</button>
    </form>
    <div id="answer"></div>
    <script>
        function ask() {
            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: document.getElementById('question').value})
            })
            .then(r => r.json())
            .then(data => document.getElementById('answer').innerText = data.answer || data.error);
        }
    </script>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
