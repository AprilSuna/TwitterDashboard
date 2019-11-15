from flask import Flask, render_template, redirect, request, session
from util.functions import *
from util.StreamListener import StreamListener
from googleapiclient import discovery
from google.cloud import datastore
import pandas as pd
import tweepy, logging

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'
perspective_api_key = 'AIzaSyAQzy172qDSsB89r-8sKcRKoLKncsHq8eU'

callback_uri = 'https://twitterdashboard.appspot.com/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'

datastore_client = datastore.Client('twitterdashboard')
service = discovery.build('commentanalyzer', 'v1alpha1', developerKey=perspective_api_key)
app = Flask(__name__)
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'


@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)


@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    loaded = False
    if request.method == 'POST':
        session['username'] = request.form.get("username")
        session['password'] = request.form.get("password")
        if len(session['username']) != 0:
            loaded = True
            key = datastore_client.key("user", session['username'])
            entity = datastore_client.get(key)
            print(entity)
            if not entity:
                print('Invalid username')
                error = "No username found"
                loaded = False
            elif entity["saltedPw"] != hash_pbkdf2(session['password'], entity['salt']):
                print('Invalid password')
                error = "Please use make sure your password is correct!"
                loaded = False
    if loaded:
        return redirect('/dash')
    else:
        return render_template('login.html', error=error)


# @app.route('/logout')
# def logout():
#     session.pop('logged_in', None)
#     return redirect('/')


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


@app.route('/app', methods=['POST', 'GET'])
def initial():
    # set up search api
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    if request.method == 'POST':
        muted = []
        for i, t in enumerate(session['tweet_replies']):
            nameM = 'mute' + str(i)
            mute = int(request.form[nameM])
            if mute:
                print('User selected mute!', t[0]['reply_user_id'])
                muted_user = api.create_mute(t[0]['reply_user_id'])
                muted.append(muted_user.id_str)
            # store_label(
            #     datastore_client, 
            #     tweet_replies[i]['reply_id'], 
            #     Mute
            # )
        print('users muted in labeling session:', muted)
        store_bm(api, datastore_client, session['user_id'])
        del session['tweet_replies']
        return redirect('/dash')

    else:        
        # set up streaming api with new thread
        print('start streaming for', session['username'])
        stream = tweepy.Stream(auth=api.auth, listener=StreamListener(service, datastore_client))
        user = api.get_user(screen_name=session['username'])
        session['user_id'] = user.id_str
        stream.filter(follow=[user.id_str], is_async=True)
        # update user profile table with user twitter id (needed for cron job)
        print('update local user with twitter id')
        user_key = datastore_client.key('user', session['username'])
        local_user = datastore_client.get(user_key)
        try:
            local_user['twitter_id'] = user.id_str
            datastore_client.put(local_user)
        except:
            print('error')

        # get initial block and mute ids, store to db for further update
        # also needed for network feature extraction
        bm_ids = store_bm(api, datastore_client, user.id_str)
        # scrape initial set of tweets for labeling
        tweet_replies = get_initial_tweets(api, datastore_client, screen_name=session['username'], count=10, service=service)
        session['tweet_replies'] = tweet_replies
        # check how many friends of the reply user is muted by the poster
        reply_user_ids = list(set([t[0]['reply_user_id'] for t in tweet_replies]))
        store_replier_network(api, datastore_client, user.id_str, reply_user_ids, bm_ids)

        for t in tweet_replies: # t = list of dict
            reply_user_id = t[0]['reply_user_id']
            reply_user_info = api.get_user(reply_user_id)
            t[0]['profile_image_url'] = reply_user_info.profile_image_url
            t[0]['description'] = reply_user_info.description

        return render_template('app.html',
                           username=session['username'],
                           length=len(tweet_replies),
                           tweet_replies=tweet_replies,
                           title='self-label')


# @app.route('/cron/bm')
# def cron_bm():
#     print('==================== enter cron ====================')
#     user_list, token_list, secret_list = [], [], []
#     query = datastore_client.query(kind='user_file')
#     local_users = query.fetch()
#     # if len(local_users) <= 0: # type is iterator (of course it is)
#     #     print('return?')
#     #     return
#     for user in local_users:
#         user_list.append(user['twitter_id'])
#         token_list.append(user['access_token'])
#         secret_list.append(user['access_token_secret'])
#         # assert
#     print('# total users:', len(user_list))
#     for user in list(zip(user_list, token_list, secret_list)):
#         user_id, token, token_secret = user 
#         auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
#         auth.set_access_token(token, token_secret)
#         api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
#         bm_ids = set()
#         for i in api.blocks_ids():
#             bm_ids.add(str(i))
#         for i in api.mutes_ids():
#             bm_ids.add(str(i))   
#         key = datastore_client.key('bm', user_id)
#         entity = datastore_client.get(key)
#         # if not entity:
#         #     print('== initial store ==')
#         #     kind = 'bm' 
#         #     name = user_id
#         #     bm_key = datastore_client.key(kind, name)
#         #     entity = datastore.Entity(key=bm_key)
#         # else:
#         #     print('== update bm ==')
#         entity['bm_ids'] = list(bm_ids) 
#         datastore_client.put(entity)
#         print('Saved', entity.key.kind, entity.key.name, entity['bm_ids'])
#     return None

# fake display user/label pair from models
# returning user should directly start with login->dash (that's why need to set up api)
@app.route("/dash")
def dash():
    if 'token' in session:
        print('get tokens from session')
        token, token_secret = session['token']
    else:
        key = datastore_client.key('user', session['username'])
        local_user = datastore_client.get(key)
        token, token_secret = local_user['access_token'], local_user['access_token_secret']
        print('get tokens from db')
        # token, token_secret = access_token, access_token_secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    user = api.get_user(screen_name=session['username']) # session['username'] from login

    key = datastore_client.key('bm', user.id_str)
    entity = datastore_client.get(key)
    muted_users = api.lookup_users(entity['bm_ids']) # list of user object (dict)
    # bm_ids = ['983642989959331840', '380749300', '44084633', '47459700', '15425377', '2316897812', '831732636070600706', '210927444']
    # muted_users = api.lookup_users(bm_ids)
    result = []
    for mu in muted_users:
        print('muted id:', mu.id_str)
        res = {}
        res['profile_image_url_https'] = mu.profile_image_url_https
        res['screen_name'] = mu.screen_name
        res['description'] = mu.description
        friendship = api.show_friendship(source_id=user.id_str, target_id=mu.id_str)[0]
        res['following'] = friendship.following
        res['followed_by'] = friendship.followed_by
        result.append(res)

    return render_template('dash.html', len=len(muted_users), result=result)

@app.route('/logout')
def sign_out():
    session.pop('username')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
