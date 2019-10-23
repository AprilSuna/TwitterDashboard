from flask import Flask, render_template, redirect, request, session
from util.functions import *
from util.StreamListener import StreamListener
from googleapiclient import discovery
from google.cloud import datastore
import pandas as pd
import tweepy, logging
from flask_paginate import Pagination

datastore_client = datastore.Client('twitterdashboard')

app = Flask(__name__)
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'

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
def initial():
    # TODO: Change to Mute labeling!!!
    if request.method == 'POST':
        if len(tweet_replies) != 0:
            for i in range(len(tweet_replies)):
                nameH = 'Harassment' + str(i)
                nameD = 'Directed' + str(i)
                # tweet_replies[i]['Harassment'] = request.form[nameH]
                # tweet_replies[i]['Directed'] = request.form[nameD]
                Harassment = request.form[nameH]
                Directed = request.form[nameD]
                print('User Print Here!')
                print(Harassment, Directed)
                store_label(
                    datastore_client, 
                    tweet_replies[i]['reply_id'], 
                    Harassment,
                    Directed
                )
    else:
        # set up search api
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        # set up streaming api with new thread
        print('start streaming for', session['username'])
        stream = tweepy.Stream(auth=api.auth, listener=StreamListener(service, datastore_client))
        user = api.get_user(screen_name=session['username'])
        stream.filter(follow=[user.id_str], is_async=True)
        # update user profile table with user twitter id (needed for cron job)
        print('update local user with twitter id')
        user_key = datastore_client.key('user_file', session['username'])
        local_user = datastore_client.get(user_key)
        try:
            local_user['twitter_id'] = user.id_str
            datastore_client.put(local_user)
        except:
            print('error')

        # # get initial block and mute ids
        # bm_ids = set()
        # for i in api.blocks_ids():
        #     bm_ids.add(str(i))
        # for i in api.mutes_ids():
        #     bm_ids.add(str(i))
        # # store to db for further update
        # store_bm(datastore_client, user.id_str, bm_ids)
        # scrape initial set of tweets for labeling
        tweet_replies = get_initial_tweets(api, screen_name=session['username'], count=10, service=service, client=datastore_client)

    # Methos = get here!
        if len(tweet_replies) != 0:
            page = int(request.args.get('page', 1))
            per_page = 1
            offset = (page - 1) * per_page

            search = False
            q = request.args.get('q')
            if q:
                search = True
            (pagination_tweet, number) = get_users(tweet_replies, offset=offset, per_page=per_page)
            pagination = Pagination(
                page=page, per_page=per_page, total=len(tweet_replies),
                css_framework='bootstrap3')
            return render_template('app.html',
                                username=session['username'],
                                len=len(pagination_tweet),
                                users=pagination_tweet,
                                page=page,
                                per_page=per_page,
                                pagination=pagination
                                )
        # TODO: how to deal w/ ?
        else:
            return render_template('app.html',
                username=session['username'],
                                len=len(pagination_tweet),
                                users=pagination_tweet,
                                page=page,
                                per_page=per_page,
                                pagination=pagination)

        # TODO 10.17: if method == 'POST'
        # add new muted to muted list

@app.route('/cron/bm') # can we pass argument to cron functions? and let it cron in separate threads
def cron_bm():
    print('==================== enter cron ====================')
    # user_list, token_list, secret_list = [], [], []
    # query = datastore_client.query(kind='user_file')
    # local_users = query.fetch()
    # # if len(local_users) <= 0: # type is iterator (of course it is)
    # #     print('return?')
    # #     return
    # for user in local_users:
    #     user_list.append(user['twitter_id'])
    #     token_list.append(user['access_token'])
    #     secret_list.append(user['access_token_secret'])
    #     # assert
    # print('# total users:', len(user_list))
    # for user in list(zip(user_list, token_list, secret_list)):
    #     user_id, token, token_secret = user 
    #     auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    #     auth.set_access_token(token, token_secret)
    #     api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    #     bm_ids = set()
    #     for i in api.blocks_ids():
    #         bm_ids.add(str(i))
    #     for i in api.mutes_ids():
    #         bm_ids.add(str(i))   
    #     key = datastore_client.key('bm', user_id)
    #     entity = datastore_client.get(key)
    #     if not entity:
    #         print('== initial store ==')
    #         kind = 'bm' 
    #         name = user_id
    #         bm_key = datastore_client.key(kind, name)
    #         entity = datastore.Entity(key=bm_key)
    #     else:
    #         print('== update bm ==')
    #     entity['bm_ids'] = list(bm_ids) 
    #     datastore_client.put(entity)
    #     print('Saved', entity.key.kind, entity.key.name, entity['bm_ids'])
    return


@app.route("/dash")
def dash():
    return render_template('dash.html', len=1, result=[])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)