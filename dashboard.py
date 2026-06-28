from flask import Flask
app = Flask('')
@app.route('/')
def home():
    return "<h1>A2 OWO FARMER</h1><p>Made by Ayush Rajdev &amp; Anzar Iqbal</p><p>Bot is running!</p>"
if __name__ == "__main__":
    print("Dashboard on http://0.0.0.0:6909")
    app.run(host='0.0.0.0', port=6909)
