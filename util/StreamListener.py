import tweepy
from . functions import get_perspective, store_reply, store_tweet 

class StreamListener(tweepy.StreamListener):
    def __init__(self, service, client):
        super(StreamListener, self).__init__()
        self.service = service
        self.client = client

    def on_status(self, status):
        if status.in_reply_to_user_id_str is not None:
            print('is_reply')
            key = self.client.key(status.in_reply_to_user_id_str, status.in_reply_to_status_id_str) # context uid, tid
            context = self.client.get(key)
            toxic_dict = get_perspective(self.service, status.text)
            store_reply(self.client,
                        reply_to_id=status.in_reply_to_user_id_str, 
                        reply_to_name=status.in_reply_to_screen_name, 
                        context_id=status.in_reply_to_status_id_str, 
                        context=context['tweet'], 
                        context_hashtags=context['tweet_hashtags'], 
                        reply_user_id=status.user.id_str, 
                        reply_user_name=status.user.screen_name, 
                        reply_id=status.id_str, 
                        text=status.text, 
                        reply_hashtags=status.entities['hashtags'],
                        toxicity=toxic_dict['toxicity'], 
                        identity_attack=toxic_dict['identity_attack'], 
                        insult=toxic_dict['insult'], 
                        profanity=toxic_dict['profanity'], 
                        threat=toxic_dict['threat'], 
                        sexually_explicit=toxic_dict['sexually_explicit'], 
                        flirtation=toxic_dict['flirtation'])
            # either pass to model now or run cron job (tensor) on training model
        else:
            store_tweet(self.client, 
                        user_id=status.user.id_str,
                        tweet_id=status.id_str,
                        user_name=status.user.screen_name,
                        tweet=status.text,
                        tweet_hashtags=status.entities['hashtags'])




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