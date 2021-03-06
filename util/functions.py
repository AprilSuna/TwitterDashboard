from google.cloud import datastore
from hashlib import pbkdf2_hmac
from random import getrandbits
import tweepy
# from google.appengine.api import urlfetch
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import pandas as pd
from pprint import pprint
import time


def get_users(users, offset, per_page):
    return (users[offset: offset + per_page], offset)

def alreadyExist(client, username):
    key = client.key('user_file', username)
    entity = client.get(key)
    if not entity:
        return False
    else:
        return True
      
def store_user_profile(client, username, password, access_token, access_token_secret):
    kind = 'user'
    name = username
    task_key = client.key(kind, name)
    entity = datastore.Entity(key=task_key)
    salt = random_salt()
    saltedPw = hash_pbkdf2(password, salt)
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

def get_initial_tweets(api, client, screen_name, count, service): 
    print('==================== get_initial_tweets ====================')
    # only select tweets that have replies (would be hard for testing)
    tweets = api.user_timeline(screen_name=screen_name, count=count) # max count = 200
    tweet_replies = []
    for tweet in tweets:
        for reply in tweepy.Cursor(api.search, q=screen_name, since_id=tweet.id_str, result_type="mixed").items(5):
            if reply.in_reply_to_status_id_str == tweet.id_str: 
                tmp = get_perspective(service, reply.text)
                if not tmp:
                    tmp = {}                
                    tmp['toxicity'] = 0.0
                    tmp['identity_attack'] = 0.0
                    tmp['insult'] = 0.0
                    tmp['profanity'] = 0.0
                    tmp['threat'] = 0.0
                    tmp['sexually_explicit'] = 0.0
                    tmp['flirtation'] = 0.0 
                assert reply.in_reply_to_status_id_str == tweet.id_str
                tmp['reply_to_name'] = reply.in_reply_to_screen_name
                tmp['context'] = tweet.text
                tmp['reply_user_id'] = reply.user.id_str # not for display, for sampling by user
                tmp['reply_user_name'] = reply.user.screen_name
                tmp['text'] = reply.text
                # print('==================== tmp ====================')
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

    # option 2: group by reply users
    tweet_replies = get_samples_2(tweet_replies)
    pprint(tweet_replies)
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
    tweet_replies = tweet_replies.groupby('reply_user_id').apply(lambda x: x.sample(frac=1))
    reply_user_ids = list(set(tweet_replies['reply_user_id'].tolist()))
    res = []
    for ruid in reply_user_ids:
        res.append(tweet_replies[tweet_replies['reply_user_id']==ruid].to_dict('records'))
    return res # list of (list of dict = tweet replies for same ruid)

def store_bm(api, client, user_id):
    print('==================== store_bm ====================')
    bm_ids = set()
    for i in api.blocks_ids():
        bm_ids.add(str(i))
    for i in api.mutes_ids():
        bm_ids.add(str(i))
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
    return bm_ids # type is set

def store_replier_network(api, client, user_id, reply_user_ids, bm_ids):
    print('bm_ids:', bm_ids)
    muted_friend_counts = []
    for ruid in reply_user_ids:
        friends = api.friends_ids(id=ruid) # followed by ruid, type=int
        # for testing
        # print('#followed by ruid:', len(friends))
        # if ruid == '1174782029617082368':
        #     pprint(friends)
        muted = set([str(fid) for fid in friends]).intersection(bm_ids)
        muted_friend_counts.append(len(muted))
    assert len(muted_friend_counts) == len(reply_user_ids)
    # save reply user network feature to database
    for ruid, cnt in list(zip(reply_user_ids, muted_friend_counts)):
        kind = user_id
        name = ruid
        task_key = client.key(kind, name)
        entity = datastore.Entity(key=task_key)
        # entity = {}
        # entity['kind'] = kind
        # entity['name'] = name
        entity['muted_friend_counts'] = cnt
        client.put(entity)
        print('Saved', entity.key.kind, entity.key.name, entity['muted_friend_counts'])
        # pprint(entity)
    
def store_label(client, reply_id, Mute):
    kind = 'tweets'
    name = reply_id
    task_key = client.key(kind, name)
    entity = client.get(task_key)
    entity['Mute'] = Mute
    client.put(entity)
    print('Saved Label', entity.key.name, entity)


from random import sample
def store_user_mock(client, user_id, user_name, service):
    query = client.query(kind='mock_new')
    query.distinct_on = ['reply_user_id']
    query.projection = ['reply_user_id']
    results = list(query.fetch())
    print('{} unique repliers'.format(len(results)))
    # print(results[:3])
    
    chosen = sample(results, 3)
    cnt = 0
    for replier in chosen:
        cnt += 1
        query = client.query(kind='mock_new')
        query.add_filter('reply_user_id', '=', replier['reply_user_id'])
        results = list(query.fetch())
        print('{} replies from user {}'.format(len(results), replier['reply_user_id']))
        # print(results[0])

        for reply in results:
            task_key = client.key(user_id, reply['reply_id'])
            entity = datastore.Entity(key=task_key)
            entity['reply_to_name'] = reply['reply_to_name']
            entity['context_id'] = reply['context_id']
            entity['context'] = reply['context']
            entity['reply_user_id'] = reply['reply_user_id']
            entity['reply_user_name'] = reply['reply_user_name']
            # entity['reply_id'] = row['reply_id']
            entity['text'] = reply['text']
            entity['reply_to_name'] = user_name

            tmp = get_perspective(service, reply['text'])
            for tox, value in tmp.items():
                entity[tox] = value

            client.put(entity)

    print('inserted {} users\' replies'.format(cnt))
