import tweepy
class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        id_str = status.id_str
        text = status.text
        # hashtags = status.entities.hashtags
        # symbols = status.entities.symbols
        # user_mentions = status.entities.user_mentions
        # in_reply_to_screen_name = status.in_reply_to_screen_name
        # in_reply_to_status_id_str = status.in_reply_to_status_id_str
        in_reply_to_user_id_str = status.in_reply_to_user_id_str
        user_id_str = status.user.id_str
        # user_screen_name = status.user.screen_name
        # user_description = status.user.description
        is_reply = False
        if in_reply_to_user_id_str is not None:
            is_reply = True
            print('is_reply')
            muted_user = api.create_mute(user_id_str)
            print('muted', user_id_str)
        print(status.text)




# def get_tweets():
#     # user's first visit to our service
#     # redirected from auth
#     # get tokens directly from session 
#     # if request.referrer == 'auth':
#     if session['token']:
#         token, token_secret = session['token']
#     else:
#         # query tokens from datastore with session username and password
#         key = datastore_client.key("user_file", session['username'])
#         entity = datastore_client.get(key)
#         token, token_secret = entity['access_token'], entity['access_token_secret']

#     auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
#     auth.set_access_token(token, token_secret)
#     api = tweepy.API(auth)

#     # set up streaming api
#     # using username as screen_name, have to ensure they are the same!!
#     if not session['token']:
#         print('start streaming')
#         stream = tweepy.Stream(auth=api.auth, listener=StreamListener())
#         user = api.get_user(screen_name=session['username'])
#         stream.filter(follow=[user.id_str], is_async=True)

#         # save to datastore
#         # change in StreamListener class

#     # search api
#     # get initial tweets for labeling
#     if session['token']:
#         print('first time user:', session['username'])
#         tweets = api.user_timeline(screen_name=session['username'], count=10) # max count = 200
#         tweet_replies = []
        
#         for tweet in tweets:
#             tmp = {}
#             tmp['tid'] = tweet.id
#             tmp['context'] = tweet.text
#             tmp['hashtag'] = tweet.entities['hashtags']
#             tmp['reply'] = []
#             for reply in tweepy.Cursor(api.search, q=session['username'], since_id=tweet.id_str, result_type="mixed", count=10).items(10):
#                 tmp['reply'].append({'uid': reply.user.id, 'uname': reply.user.name, 'reply': reply.text})
#                 tweet_replies.append(tmp)
#         # print(tweets)
#         print(tweet_replies)

#     # save to db and display for labeling

#     return render_template('app.html')