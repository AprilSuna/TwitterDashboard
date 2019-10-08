from flask import render_template, Flask, redirect, request, session
from google.cloud import datastore
from util.functions import alreadyExist, store_user_profile, random_salt, hash_pbkdf2, store_tweets
import tweepy, logging
from util.StreamListener import StreamListener

datastore_client = datastore.Client('twitterdashboard')

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
    return render_template('index.html')
#     tweet_replies = [
#         {'tid': 1181568448004050951, 
#         'context': 'As President, I leaned on @AmbassadorRice’s experience, expertise, and willingness to tell me what I needed to hear… https://t.co/oWx2obfDF5', 'hashtag': [], 
#         'reply': {'uid': 1174477973879238657, 'uname': 'mpy', 'reply': '@BarackObama \nObama still control mainstream media and many federal government agencies. the media is party of the… https://t.co/dZsNVllSfW'}}, 
#         {'tid': 1181568448004050951, 'context': 'As President, I leaned on @AmbassadorRice’s experience, expertise, and willingness to tell me what I needed to hear… https://t.co/oWx2obfDF5', 'hashtag': [], 
#         'reply': {'uid': 51639017, 'uname': 'Valerie Cartwright',
#          'reply': 'RT @ReasePaino: @BarackObama @AmbassadorRice https://t.co/NjZFQ2HD0Y'}}
#         ]
#     return render_template('dash.html', len = len(tweet_replies), result = tweet_replies)


@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    loaded = False
    if request.method == 'POST':
        session['username'] = request.form.get("username")
        session['password'] = request.form.get("password")
        if len(session['username']) != 0:
            loaded = True
            key = datastore_client.key("user_file", session['username'])
            entity = datastore_client.get(key)
            print(entity)
            if not entity:
                print("No username found")
                error = 'Invalid username'
                loaded = False
            elif entity["saltedPw"] != hash_pbkdf2(session['password'], entity['salt']):
                print("Please use make sure your password is correct!")
                error = 'Invalid password'
                loaded = False
    if loaded:
      return redirect('/dash')
    else:
        return render_template('login.html', error=error)


@app.route("/register", methods=['POST', 'GET'])
def register():
    error = None
    loaded = False
    if request.method == 'POST':
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')
        rePassword = request.form.get("password-repeat")
        if len(session['username']) != 0:
            loaded = True
            if session['password'] != rePassword:
                error = "Make sure the passwords match with each other."
                loaded = False
            if alreadyExist(datastore_client, session['username']):
                error = "Ooops! The username has already exist, please use another!"
                loaded = False
            # store_user_profile(datastore_client, session['username'], session['password'])
    if loaded:
        return redirect('/auth')
    else:
        return render_template('register.html', error=error)


@app.route("/auth", methods=['POST', 'GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()

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
    store_user_profile(datastore_client, session['username'], session['password'], auth.access_token, auth.access_token_secret)

    return redirect('/app')


@app.route('/app') # rate limit, might use stream api
def get_tweets(): # old version in StreamListener
    token, token_secret = session['token']

    # set up search api
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)

    # set up streaming api with new thread
    print('start streaming for', session['username'])
    stream = tweepy.Stream(auth=api.auth, listener=StreamListener())
    user = api.get_user(screen_name=session['username'])
    stream.filter(follow=[user.id_str], is_async=True)

    # scrape initial set of tweets
    # only select tweets that have replies (would be hard for testing)
    tweets = api.user_timeline(screen_name=session['username'], count=10) # max count = 200
    tweet_replies = []
    for tweet in tweets:
        tmp = {}
        tmp['tid'] = tweet.id_str
        tmp['context'] = tweet.text
        tmp['hashtag'] = tweet.entities['hashtags']
        tmp['reply'] = []
        for reply in tweepy.Cursor(api.search, q=session['username'], since_id=tweet.id_str, result_type="mixed", count=2).items(2):
            if reply.in_reply_to_status_id_str == tweet.id_str:
                tmp['reply']= {'uid': reply.user.id_str, 'uname': reply.user.screen_name, 'reply': reply.text}
    #           tweet_replies used for display in dash.html
                tweet_replies.append(tmp.copy())
    #           store to database & for training
                store_tweets(datastore_client, tweet.id_str, 
                            reply_to_id=tweet.user.id_str,
                            reply_to_name=session['username'], 
                            context=tweet.text, 
                            context_hashtags=tweet.entities['hashtags'], 
                            reply_id=reply.id_str,
                            reply_user_id=reply.user.id_str, 
                            reply_user_name=reply.user.screen_name, 
                            text=reply.text)
    print(tweet_replies)

    # display for label
    # return render_template('app.html')
    # after labeling
    return render_template('dash.html', len = len(tweet_replies), result = tweet_replies)

                    
@app.route("/dash")
def dash():
    return render_template('dash.html', len=1, result = [])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
