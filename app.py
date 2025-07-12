from flask import Flask, request, jsonify
from chatbot import BajajFinservChatbot

app = Flask(__name__)
bot = BajajFinservChatbot()
bot.load_documents("data/")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    response = bot.chat(data["query"])
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(port=5000)