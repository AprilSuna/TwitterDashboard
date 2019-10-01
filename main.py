from flask import render_template, Flask, redirect, request
from google.cloud import datastore
from util.hash import random_salt, hash_pbkdf2
from util.functions import alreadyExist
import tweepy

datastore_client = datastore.Client('twitterdashboard')


def store_user_profile(username, password):
    kind = 'user_file'
    name = username
    task_key = datastore_client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    salt = random_salt()
    saltedPw = hash_pbkdf2(password, salt)
    entity['username'] = username
    entity['saltedPw'] = saltedPw
    entity['salt'] = salt
    datastore_client.put(entity)
    print('Saved {}: {}'.format(entity.key.name, entity['saltedPw']))


app = Flask(__name__)
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SECRET_KEY'] = 'redsfsfsfsfis'
# sess = Session()
# sess.init_app(app)

# april's tokens
# access_token = '1106277569752633351-z9XGTbAL7ZxEqT7aToonp8NvO4XuQJ'
# access_token_secret = 'EEKofWc9VV0a4V16wtdAoPSvZHbhZtriyZgKZTf20M7Bq'
# consumer_key = '8lkEPXD9VBXwNxES21RR8k0vZ'
# consumer_secret = 'hkLL9WWMnhbz7trMlfIOgzyctXayT1ZzUYilmdWi16xEhJs4FM'

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'

callback_uri = 'https://localhost:8080/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)


@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            print(username, password)
            key = datastore_client.key("user_file", username)
            entity = datastore_client.get(key)
            print(entity)
            if not entity:
                print("No username found")
                error = 'Invalid username'
            elif entity["saltedPw"] != hash_pbkdf2(password, entity['saltedPw']):
                print("Please use make sure your password is correct!")
                error = 'Invalid password'
    return render_template('login.html', error=error)


@app.route("/register", methods=['POST', 'GET'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        rePassword = request.form.get("password-repeat")
        if username and password:
            if password != rePassword:
                error = "Make sure the passwords match with each other."
            if alreadyExist(username):
                error = "Ooops! The username has already exit, please use another!"
            print(username, password)
            print(type(username), type(password))
            store_user_profile(str(username), str(password))
    return render_template('register.html', error=error)
    # return redirect('/auth')


@app.errorhandler(404)
def not_found(e):
    return render_template('custom_page.html'), 404


@app.route("/auth", methods=['POST', 'GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()
    print(redirect_url)
    print(auth.request_token)
    session['request_token'] = auth.request_token

    return redirect(redirect_url)


@app.route("/callback",methods=['POST','GET'])
def callback():
    request_token = session['request_token']
    del session['request_token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    print(auth.access_token, auth.access_token_secret)

    return redirect('/index')


if __name__ == '__main__':
    app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'
    app.run(host='127.0.0.1', port=8080,  debug=True)
