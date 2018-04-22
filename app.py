from flask import Flask,render_template
import requests
from requests_oauthlib import OAuth1
from urllib.parse import parse_qs
import os
app = Flask(__name__)	

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHENTICATE_URL = "https://api.twitter.com/oauth/authenticate?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

@app.route('/')
def inicio():
	return render_template("inicio.html")

## oauth1

def get_request_token_oauth1():
    print(os.environ["CONSUMER_KEY"])
    print(os.environ["CONSUMER_SECRET"])
    oauth = OAuth1(os.environ["CONSUMER_KEY"],
                   client_secret=os.environ["CONSUMER_SECRET"])
    print(REQUEST_TOKEN_URL)
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    print(r)
    credentials = parse_qs(r.content)
    print (credentials)
    return credentials.get('oauth_token')[0],credentials.get('oauth_token_secret')[0]

@app.route('/twitter')
def twutter():
	request_token,request_token_secret = get_request_token_oauth1()
	print(request_token,request_token_secret)

if __name__ == '__main__':
	port=os.environ["PORT"]
	app.run('0.0.0.0',int(port), debug=True)