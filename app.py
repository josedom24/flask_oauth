from flask import Flask,render_template,redirect,request
import requests
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from urllib.parse import parse_qs
import os,json
app = Flask(__name__)   

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHENTICATE_URL = "https://api.twitter.com/oauth/authenticate?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

@app.route('/')
def inicio():
    return render_template("inicio.html")

## oauth1

def get_request_token_oauth1():
    oauth = OAuth1(os.environ["CONSUMER_KEY"],
                  client_secret=os.environ["CONSUMER_SECRET"])
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    return credentials.get(b'oauth_token')[0],credentials.get(b'oauth_token_secret')[0]

def get_access_token_oauth1(request_token,request_token_secret,verifier):
    oauth = OAuth1(os.environ["CONSUMER_KEY"],
                   client_secret=os.environ["CONSUMER_SECRET"],
                   resource_owner_key=request_token,
                   resource_owner_secret=request_token_secret,
                   verifier=verifier,)
  
      
    r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    return credentials.get(b'oauth_token')[0],credentials.get(b'oauth_token_secret')[0]

@app.route('/twitter')
def twitter():
    request_token,request_token_secret = get_request_token_oauth1()
    authorize_url = AUTHENTICATE_URL + request_token.decode("utf-8")
    plantilla=render_template("oauth1.html",authorize_url=authorize_url)
    response = app.make_response(plantilla)  
    response.set_cookie('request_token',value=request_token.decode("utf-8"))
    response.set_cookie('request_token_secret',value=request_token_secret.decode("utf-8"))
    return response

@app.route('/twitter_callback')
def twitter_callback():
    request_token=request.cookies.get("request_token")
    request_token_secret=request.cookies.get("request_token_secret")
    verifier  = request.args.get("oauth_verifier")
    access_token,access_token_secret= get_access_token_oauth1(request_token,request_token_secret,verifier)
    plantilla=redirect('/vertweet')  
    response = app.make_response(plantilla) 
    response.set_cookie("access_token", access_token.decode("utf-8"))
    response.set_cookie("access_token_secret", access_token_secret.decode("utf-8"))
    return response

@app.route('/vertweet')
def vertweet():
    access_token=request.cookies.get("access_token")
    access_token_secret=request.cookies.get("access_token_secret")
    oauth = OAuth1(os.environ["CONSUMER_KEY"],
                   client_secret=os.environ["CONSUMER_SECRET"],
                   resource_owner_key=access_token,
                   resource_owner_secret=access_token_secret)
    url = 'https://api.twitter.com/1.1/statuses/home_timeline.json'
    r = requests.get(url=url,auth=oauth)
    if r.status_code==200:
        return render_template("vertweet.html",datos=r.json())
    else:
        return redirect("/twitter")


#### Oauth2

redirect_uri = 'https://oauth-jd.herokuapp.com/google_callback'
scope = ['https://www.googleapis.com/auth/userinfo.profile']
token_url = "https://accounts.google.com/o/oauth2/token"

@app.route('/google')
def google():
    return render_template("oauth2.html")
 
def token_valido():
    token=json.loads(request.cookies.get("token"))
    if token:
        token_ok = True
        try:
            oauth2 = OAuth2Session(os.environ["client_id"], token=token)
            r = oauth2.get('https://www.googleapis.com/oauth2/v1/userinfo')
        except TokenExpiredError as e:
            token_ok = False
    else:
        token_ok = False
    return token_ok

@app.route('/perfil')
def info_perfil():
  print(request.url)  
  if token_valido():
    redirect("/perfil_usuario")
  else:
    oauth2 = OAuth2Session(os.environ["client_id"], redirect_uri=redirect_uri,scope=scope)
    authorization_url, state = oauth2.authorization_url('https://accounts.google.com/o/oauth2/auth')
    plantilla=redirect(authorization_url)  
    response = app.make_response(plantilla) 
    response.set_cookie("token", value="",expires=0)
    response.set_cookie("oauth_state", value=state)
    return response

@app.route('/google_callback')
def get_token():
    print(request.url)
    oauth2 = OAuth2Session(os.environ["client_id"], state=request.cookies.get("oauth_state"),redirect_uri=redirect_uri)
    token = oauth2.fetch_token(token_url, client_secret=os.environ["client_secret"],authorization_response=request.url[:4]+"s"+request.url[4:])
    plantilla=redirect("/perfil_usuario")
    response = app.make_response(plantilla) 
    response.set_cookie("token",value=json.dumps(token))
    return response

@app.route('/perfil_usuario')
def info_perfil_usuario():
    if token_valido():
        token=json.loads(request.cookies.get("token"))
        oauth2 = OAuth2Session(os.environ["client_id"], token=token)
        r = oauth2.get('https://www.googleapis.com/oauth2/v1/userinfo')
        doc=json.loads(r.content)
        return '<p>%s</p><img src="%s"/><br/><a href="/logout">Cerrar</a>' % (doc["name"],doc["picture"])
    else:
        redirect('/perfil')

if __name__ == '__main__':
    port=os.environ["PORT"]
    app.run('0.0.0.0',int(port), debug=True)