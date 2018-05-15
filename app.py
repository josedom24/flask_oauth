from flask import Flask,render_template,redirect,request,session
import requests
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from urllib.parse import parse_qs
import os,json
app = Flask(__name__)   
app.secret_key= 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


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
    session["request_token"]=request_token.decode("utf-8")
    session["request_token_secret"]=request_token_secret.decode("utf-8")
    return render_template("oauth1.html",authorize_url=authorize_url)

@app.route('/twitter_callback')
def twitter_callback():
    request_token=session["request_token"]
    request_token_secret=session["request_token_secret"]
    verifier  = request.args.get("oauth_verifier")
    access_token,access_token_secret= get_access_token_oauth1(request_token,request_token_secret,verifier)
    session["access_token"]= access_token.decode("utf-8")
    session["access_token_secret"]= access_token_secret.decode("utf-8")
    return redirect('/vertweet')

@app.route('/vertweet')
def vertweet():
    access_token=session["access_token"]
    access_token_secret=session["access_token_secret"]
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
    try:
        token=json.loads(session["token"])
    except:
        token = False
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
  if token_valido():
    return redirect("/perfil_usuario")
  else:
    oauth2 = OAuth2Session(os.environ["client_id"], redirect_uri=redirect_uri,scope=scope)
    authorization_url, state = oauth2.authorization_url('https://accounts.google.com/o/oauth2/auth')
    session.pop("token",None)
    session["oauth_state"]=state
    return redirect(authorization_url)  

@app.route('/google_callback')
def get_token():
    oauth2 = OAuth2Session(os.environ["client_id"], state=session["oauth_state"],redirect_uri=redirect_uri)
    token = oauth2.fetch_token(token_url, client_secret=os.environ["client_secret"],authorization_response=request.url[:4]+"s"+request.url[4:])
    session["token"]=json.dumps(token)
    return redirect("/perfil_usuario")

@app.route('/perfil_usuario')
def info_perfil_usuario():
    if token_valido():
        token=json.loads(session["token"])
        oauth2 = OAuth2Session(os.environ["client_id"], token=token)
        r = oauth2.get('https://www.googleapis.com/oauth2/v1/userinfo')
        doc=json.loads(r.content)
        return render_template("perfil.html", datos=doc)
    else:
        return redirect('/perfil')

@app.route('/logout')
def salir():
    session.pop("token",None)
    return redirect("/perfil")

## oauth2 spotify

redirect_uri_sp = 'https://oauth-jd.herokuapp.com/spotify_callback'
scope_sp = 'user-read-private user-read-email'
token_url_sp = "https://accounts.spotify.com/api/token"

def token_valido_spotify():
    try:
        token=json.loads(session["token_sp"])
    except:
        token = False
    if token:
        token_ok = True
        try:
            oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
            r = oauth2.get('https://api.spotify.com/v1/me')
        except TokenExpiredError as e:
            token_ok = False
    else:
        token_ok = False
    return token_ok


@app.route('/spotify')
def spotify():
    return render_template("oauth2_spotify.html")

@app.route('/perfil_spotify')
def info_perfil_spotify():
  if token_valido_spotify():
    return redirect("/perfil_usuario_spotify")
  else:
    oauth2 = OAuth2Session(os.environ["client_id_spotify"], redirect_uri=redirect_uri_sp,scope=scope_sp)
    authorization_url, state = oauth2.authorization_url('https://accounts.spotify.com/authorize')
    session.pop("token_sp",None)
    session["oauth_state_sp"]=state
    return redirect(authorization_url)  

@app.route('/spotify_callback')
def get_token_spotify():
    oauth2 = OAuth2Session(os.environ["client_id_spotify"], state=session["oauth_state_sp"],redirect_uri=redirect_uri_sp)
    print (request.url)
    token = oauth2.fetch_token(token_url_sp, client_secret=os.environ["client_secret_spotify"],authorization_response=request.url[:4]+"s"+request.url[4:])
    session["token_sp"]=json.dumps(token)
    return redirect("/perfil_usuario_spotify")

@app.route('/perfil_usuario_spotify')
def info_perfil_usuario_spotify():
    if token_valido_spotify():
        token=json.loads(session["token_sp"])
        oauth2 = OAuth2Session(os.environ["client_id_spotify"], token=token)
        r = oauth2.get('https://api.spotify.com/v1/me')
        doc=json.loads(r.content.decode("utf-8"))
        return render_template("perfil_spotify.html", datos=doc)
    else:
        return redirect('/perfil')

@app.route('/logout_spotify')
def salir_spotify():
    session.pop("token_sp",None)
    return redirect("/spotify")

if __name__ == '__main__':
    port=os.environ["PORT"]
    app.run('0.0.0.0',int(port), debug=True)