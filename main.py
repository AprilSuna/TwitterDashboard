from flask import render_template, Flask, redirect, request, session
# from google.cloud import datastore
from util.functions import random_salt, hash_pbkdf2
# , alreadyExist, store_user_profile, store_tweets
import tweepy, logging
from util.StreamListener import StreamListener
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import pandas as pd

# datastore_client = datastore.Client('twitterdashboard')

app = Flask(__name__)
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'
perspective_api_key = 'AIzaSyAQzy172qDSsB89r-8sKcRKoLKncsHq8eU'

callback_uri = 'https://aa3a6ae5.ngrok.io/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'

service = discovery.build('commentanalyzer', 'v1alpha1', developerKey=perspective_api_key)

@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html')

@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    loaded = False
    if request.method == 'POST':
        session['username'] = request.form.get("username")
        session['password'] = request.form.get("password")
        if len(session['username']) != 0:
            loaded = True
            # key = datastore_client.key("user_file", session['username'])
            # entity = datastore_client.get(key)
            # print(entity)
            # if not entity:
            #     print('Invalid username')
            #     error = "No username found"
            #     loaded = False
            # elif entity["saltedPw"] != hash_pbkdf2(session['password'], entity['salt']):
            #     print('Invalid password')
            #     error = "Please use make sure your password is correct!"
            #     loaded = False
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
            # if alreadyExist(datastore_client, session['username']):
            #     error = "Ooops! The username has already exist, please use another!"
            #     loaded = False
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
    # store_user_profile(datastore_client, session['username'], session['password'], auth.access_token, auth.access_token_secret)

    return redirect('/app')


@app.route('/app') # rate limit, might use stream api

# TODO 10.17:
# need to get previous mute list somewhere
# reform the code to include get_tweets, get_muted, etc.

def get_tweets(): # old version in StreamListener
    token, token_secret = session['token']

    # set up search api
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

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

        for reply in tweepy.Cursor(api.search, q=session['username'], since_id=tweet.id_str, result_type="mixed").items(5):
            if reply.in_reply_to_status_id_str == tweet.id_str:
                # comment = {'uid': reply.user.id_str, 'uname': reply.user.screen_name, 'reply': reply.text}
                tmp['reply_user_id'] = reply.user.id_str
                tmp['reply_user_name'] = reply.user.screen_name
                tmp['text'] = reply.text
                tmp = get_perspective(tmp)

                # tweet_replies used for display in dash.html
                tweet_replies.append(tmp.copy())
                # store to database & for training
                # store_tweets(datastore_client, '_'.join(tweet.id_str, reply.id_str), 
                #             reply_to_id=tweet.user.id_str,
                #             reply_to_name=session['username'], 
                #             context=tweet.text, 
                #             context_hashtags=tweet.entities['hashtags'], 
                #             reply_user_id=reply.user.id_str, 
                #             reply_user_name=reply.user.screen_name, 
                #             text=reply.text,
                #             reply_hashtags=reply.entities['hashtags'],
                #             toxicity=tmp['toxicity'],
                #             identity_attack=tmp['identity_attack'],
                #             insult=tmp['insult'],
                #             profanity=tmp['profanity'],
                #             threat=tmp['threat'],
                #             sexually_explicit=tmp['sexually_explicit'],
                #             flirtation=tmp['flirtation'])
    # option 1: sample by perspective scores
    # tweet_replies = get_samples_1(tweet_replies)

    # option 2: group by reply users, threshold at 5
    tweet_replies = get_samples_2(tweet_replies)
    print(tweet_replies)

    # display for label
    # return render_template('app.html')
    # after labeling
    return render_template('dash.html', len = len(tweet_replies), result = tweet_replies)
  
def get_perspective(tmp):
    analyze_request = {'comment': {'text': tmp['text']},
                        'requestedAttributes': {'TOXICITY': {}, 
                        'IDENTITY_ATTACK':{}, 
                        'INSULT':{}, 
                        'PROFANITY':{}, 
                        'THREAT':{}, 
                        'SEXUALLY_EXPLICIT':{}, 
                        'FLIRTATION':{}}}
    one_more_time = True # flag if need to sleep before getting the scores
    while one_more_time:
        one_more_time = False
        try:
            response = service.comments().analyze(body=analyze_request).execute()

            tmp['toxicity'] = response['attributeScores']['TOXICITY']['summaryScore']['value']
            tmp['identity_attack'] = response['attributeScores']['IDENTITY_ATTACK']['summaryScore']['value']
            tmp['insult'] = response['attributeScores']['INSULT']['summaryScore']['value']
            tmp['profanity'] = response['attributeScores']['PROFANITY']['summaryScore']['value']
            tmp['threat'] = response['attributeScores']['THREAT']['summaryScore']['value']
            tmp['sexually_explicit'] = response['attributeScores']['SEXUALLY_EXPLICIT']['summaryScore']['value']
            tmp['flirtation'] = response['attributeScores']['FLIRTATION']['summaryScore']['value']
            
        except HttpError as e:
            print('\n----------------------------------------------------')
            # all scores should be nan
            if e.resp.status == 429:
                one_more_time = True
                print('Sleeping...')
                time.sleep(1)
            if e.resp.status == 400:
                print(e)
                print(tmp['text'])    
    return tmp

def get_samples_1(tweet_replies):
    tweet_replies = pd.DataFrame.from_records(tweet_replies)
    samples = set()
    for type in ['toxicity', 'identity_attack', 'insult', 'profanity', 'threat', 'sexually_explicit', 'flirtation']:
        indices = tweet_replies[tweet_replies[type] > 0.5].sample(frac=1).index.values
        for idx in list(indices):
            samples.add(idx)
    tweet_replies = tweet_replies.iloc[list(samples)]
    tweet_replies = tweet_replies.to_dict('records')
    return tweet_replies

def get_samples_2(tweet_replies):
    tweet_replies = pd.DataFrame.from_records(tweet_replies)
    tweet_replies = tweet_replies.groupby('reply_user_id').apply(lambda x: x.sample(n=2))    
    tweet_replies = tweet_replies.to_dict('records')
    return tweet_replies

@app.route("/dash")
def dash():
    return render_template('dash.html', len=1, result = [])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
