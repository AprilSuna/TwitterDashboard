from google.cloud import datastore
from hashlib import pbkdf2_hmac
from random import getrandbits
import tweepy
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import pandas as pd
from pprint import pprint
import time

def alreadyExist(client, username):
    key = client.key('user_file', username)
    entity = client.get(key)
    if not entity:
        return False
    else:
        return True
      
def store_user_profile(client, username, password, access_token, access_token_secret):
    kind = 'user_file'
    name = username
    task_key = client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    salt = random_salt()
    saltedPw = hash_pbkdf2(password, salt)
    entity['username'] = username
    entity['saltedPw'] = saltedPw
    entity['salt'] = salt
    entity['access_token'] = access_token
    entity['access_token_secret'] = access_token_secret
    client.put(entity)
    print('Saved {}: {}'.format(entity.key.name, entity['saltedPw']))

def random_salt():
    return getrandbits(128).to_bytes(16, byteorder='little').hex()

def hash_pbkdf2(x, salt):
    return pbkdf2_hmac('sha256', x.encode('utf-8'), bytes.fromhex(salt), 100000).hex()

def store_reply(client, reply_to_id, reply_to_name, 
    context_id, context, context_hashtags, 
    reply_user_id, reply_user_name, reply_id, text, reply_hashtags,
    toxicity, identity_attack, insult, profanity, threat, sexually_explicit, flirtation):
    print('==================== store_reply ====================')
    kind = reply_to_id # context user id as table name
    name = reply_id  # reply id as unique identifier
    task_key = client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    # for testing
    # entity = {}
    # entity['kind'] = reply_to_id
    # entity['name'] = context_id
    entity['reply_to_name'] = reply_to_name
    entity['context_id'] = context_id
    entity['context'] = context
    entity['context_hashtags'] = context_hashtags
    entity['reply_user_id'] = reply_user_id
    entity['reply_user_name'] = reply_user_name
    # entity['reply_id'] = reply_id
    entity['text'] = text
    entity['reply_hashtags'] = reply_hashtags
    entity['toxicity'] = toxicity
    entity['identity_attack'] = identity_attack
    entity['insult'] = insult
    entity['profanity'] = profanity
    entity['threat'] = threat
    entity['sexually_explicit'] = sexually_explicit
    entity['flirtation'] = flirtation
    client.put(entity)
    print('Saved', entity.key.kind, entity.key.name, entity['text'])
    # pprint(entity)

def store_tweet(client, user_id, tweet_id, user_name, tweet, tweet_hashtags): # if it's an original tweet
    print('==================== store_tweet ====================')
    kind = user_id # poster's id
    name = tweet_id    # poster's text
    task_key = client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    # entity = {}
    # entity['kind'] = user_id
    # entity['name'] = tweet_id
    entity['screen_name'] = user_name
    entity['tweet'] = tweet
    entity['tweet_hashtags'] = tweet_hashtags
    client.put(entity)
    print('Saved', entity.key.kind, entity.key.name, entity['tweet'])
    # pprint(entity)

def get_initial_tweets(api, screen_name, count, service, client): # old version in StreamListener
    print('==================== get_initial_tweets ====================')
    # only select tweets that have replies (would be hard for testing)
    tweets = api.user_timeline(screen_name=screen_name, count=count) # max count = 200
    tweet_replies = []
    for tweet in tweets:
        for reply in tweepy.Cursor(api.search, q=screen_name, since_id=tweet.id_str, result_type="mixed").items(5):
            if reply.in_reply_to_status_id_str == tweet.id_str:                
                tmp = get_perspective(service, reply.text)
                assert reply.in_reply_to_status_id_str == tweet.id_str
                tmp['reply_to_name'] = reply.in_reply_to_screen_name
                tmp['context'] = tweet.text
                tmp['reply_user_id'] = reply.user.id_str # not for display, for sampling by user
                tmp['reply_user_name'] = reply.user.screen_name
                tmp['text'] = reply.text
                # pprint(tmp)

                # tweet_replies used for display in dash.html
                tweet_replies.append(tmp.copy())
                # store to database & for training
                store_reply(client,
                            reply_to_id=tweet.user.id_str,
                            reply_to_name=screen_name, 
                            context_id=tweet.id_str, 
                            context=tweet.text, 
                            context_hashtags=tweet.entities['hashtags'], 
                            reply_user_id=reply.user.id_str, 
                            reply_user_name=reply.user.screen_name,
                            reply_id=reply.id_str,
                            text=reply.text,
                            reply_hashtags=reply.entities['hashtags'],
                            toxicity=tmp['toxicity'],
                            identity_attack=tmp['identity_attack'],
                            insult=tmp['insult'],
                            profanity=tmp['profanity'],
                            threat=tmp['threat'],
                            sexually_explicit=tmp['sexually_explicit'],
                            flirtation=tmp['flirtation'])
    # option 1: sample by perspective scores
    # tweet_replies = get_samples_1(tweet_replies)

    # option 2: group by reply users, threshold at 5
    # tweet_replies = get_samples_2(tweet_replies)
    print(tweet_replies)
    return tweet_replies
             
def get_perspective(service, text):
    analyze_request = {'comment': {'text': text},
                        'requestedAttributes': {'TOXICITY': {}, 
                        'IDENTITY_ATTACK':{}, 
                        'INSULT':{}, 
                        'PROFANITY':{}, 
                        'THREAT':{}, 
                        'SEXUALLY_EXPLICIT':{}, 
                        'FLIRTATION':{}}}
    one_more_time = True # flag if need to sleep before getting the scores
    toxic_dict = {}
    while one_more_time:
        one_more_time = False
        try:
            response = service.comments().analyze(body=analyze_request).execute()

            toxic_dict['toxicity'] = response['attributeScores']['TOXICITY']['summaryScore']['value']
            toxic_dict['identity_attack'] = response['attributeScores']['IDENTITY_ATTACK']['summaryScore']['value']
            toxic_dict['insult'] = response['attributeScores']['INSULT']['summaryScore']['value']
            toxic_dict['profanity'] = response['attributeScores']['PROFANITY']['summaryScore']['value']
            toxic_dict['threat'] = response['attributeScores']['THREAT']['summaryScore']['value']
            toxic_dict['sexually_explicit'] = response['attributeScores']['SEXUALLY_EXPLICIT']['summaryScore']['value']
            toxic_dict['flirtation'] = response['attributeScores']['FLIRTATION']['summaryScore']['value']
            
        except HttpError as e:
            print('\n----------------------------------------------------')
            # all scores should be nan
            if e.resp.status == 429:
                one_more_time = True
                print('Sleeping...')
                time.sleep(1)
            if e.resp.status == 400:
                print(e)
                print(text)    
    return toxic_dict

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
    tweet_replies = tweet_replies.groupby('reply_user_id').apply(lambda x: x.sample(frac=0.5))    
    tweet_replies = tweet_replies.to_dict('records')
    return tweet_replies

def store_bm(client, user_id, bm_ids):
    print('==================== store_bm ====================')
    kind = 'bm' 
    name = user_id
    task_key = client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    # entity = {}
    # entity['name'] = user_id
    entity['bm_ids'] = list(bm_ids) 
    client.put(entity)
    print('Saved', entity.key.kind, entity.key.name, entity['bm_ids'])
    # pprint(entity)











