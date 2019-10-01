from flask import render_template, Flask, redirect, request
from google.cloud import datastore
from util.hash import random_salt, hash_pbkdf2
from util.functions import alreadyExist
import tweepy
from util.StreamListener import StreamListener

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
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'

callback_uri = 'https://twitterdashboard.appspot.com/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)


@app.route("/login", methods=['POST', 'GET'])
def login():
    # should redirect to app if it's not user's first visit
    # get stored username and password from datastore
    error = None
    if request.method == 'POST':
<<<<<<< HEAD
        session['username'] = request.form.get("username")
        session['password'] = request.form.get("password")
        if session['username'] and session['password']:
            key = datastore_client.key("user_file", session['username'])
            entity = datastore_client.get(key)
            if not entity:
                print("No username found")
                error = 'Invalid username'
            elif entity["saltedPw"] != hash_pbkdf2(session['password'], entity['saltedPw']):
                print("Please use make sure your password is correct!")
                error = 'Invalid password'
    return redirect('/app', error=error)
=======
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
>>>>>>> refs/remotes/origin/april


@app.route("/register", methods=['POST', 'GET'])
def register():
	error = None
    if request.method == 'POST':
<<<<<<< HEAD
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')
        rePassword = request.form.get("password-repeat")
        if session['username'] and session['password']:
            if session['password'] != rePassword:
                error = "Make sure the passwords match with each other."
            if alreadyExist(session['username']):
                error = "Ooops! The username has already exit, please use another!"
                return render_template('register.html', error=error)
            store_user_profile(session['username'], session['password'])
    # return render_template('register.html', error=error)
    return redirect('/auth', error=error)
=======
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
>>>>>>> refs/remotes/origin/april


@app.route("/auth", methods=['POST', 'GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()
<<<<<<< HEAD

    logging.info(redirect_url)
    logging.info(auth.request_token)

    session['request_token'] = auth.request_token
    return redirect(redirect_url)


@app.route("/callback", methods=['POST', 'GET'])
def callback():
    request_token = session['request_token']
    del session['request_token']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    logging.info(verifier)

    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    logging.info(auth.access_token, auth.access_token_secret)

    # save access_token, access_token_secret to datastore for reuse

    return redirect('/app')


@app.route('/app') # rate limit, might use stream api
def get_tweets():
    # user's first visit to our service
    # redirected from auth
    # get tokens directly from session 
    print(request.referrer)
    # if request.referrer == 'auth':
    if session['token']:
        token, token_secret = session['token']
    else:
        # query tokens from datastore with session username and password
        print('db needed')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)

    # set up streaming api
    # using username as screen_name, have to ensure they are the same!!
    if not session['token']:
        print('start streaming')
        stream = tweepy.Stream(auth=api.auth, listener=StreamListener())
        user = api.get_user(screen_name=screen_name)
        stream.filter(follow=[user.id_str], is_async=True)

        # save to datastore
        # change in StreamListener class

    # search api
    # get initial tweets for labeling
    if session['token']:
    	print('first time user')
	    tweets = api.user_timeline(screen_name=session['username'], count=200) # max count
	    tweet_replies = []
	    
	    for tweet in tweets:
	        tmp = {}
	        tmp['tid'] = tweet.id
	        tmp['context'] = tweet.text
	        tmp['hashtag'] = tweet.entities['hashtags']
	        tmp['reply'] = []
	        for reply in tweepy.Cursor(api.search, q=session['username'], since_id=tweet.id_str, result_type="mixed", count=10).items(10):
	            tmp['reply'].append({'uid': reply.user.id, 'uname': reply.user.name, 'reply': reply.text})
	            tweet_replies.append(tmp)
	    print(tweets)

    # save to db and display for labeling

    return render_template('app.html')
=======
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
>>>>>>> refs/remotes/origin/april


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
