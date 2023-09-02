# To test the code. Basically, run the programm by include these codes and use ngrok to connect a webhook with LINE Official Account
from pyngrok import ngrok
from flask import Flask, request, abort

app = Flask(__name__)
http_tunnel = ngrok.connect(5000) # A numbers in (5000) is your port

# Replace def lambda_handler with this part instead
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    return 'OK'

# Put this part underneath the code
if __name__ == "__main__":
    app.run()
