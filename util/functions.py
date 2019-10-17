# from google.cloud import datastore
from hashlib import pbkdf2_hmac
from random import getrandbits

def alreadyExist(client, username):
    key = client.key('user_file', username)
    entity = client.get(key)
    if not entity:
        return False
    else:
        return True

      
# def store_user_profile(client, username, password, access_token, access_token_secret):
#     kind = 'user_file'
#     name = username
#     task_key = client.key(kind, name)
#     entity = datastore.Entity(key=task_key)
#     salt = random_salt()
#     saltedPw = hash_pbkdf2(password, salt)
#     entity['username'] = username
#     entity['saltedPw'] = saltedPw
#     entity['salt'] = salt
#     entity['access_token'] = access_token
#     entity['access_token_secret'] = access_token_secret
#     client.put(entity)
#     print('Saved {}: {}'.format(entity.key.name, entity['saltedPw']))

def random_salt():
    return getrandbits(128).to_bytes(16, byteorder='little').hex()

def hash_pbkdf2(x, salt):
    return pbkdf2_hmac('sha256', x.encode('utf-8'), bytes.fromhex(salt), 100000).hex()

# def store_tweets(client, context_id, reply_to_id, reply_to_name, context, context_hashtags, reply_id, reply_user_id, reply_user_name, text):
#     kind = 'tweets'
#     name = context_id
#     task_key = client.key(kind, name)
#     entity = datastore.Entity(key=task_key)
#     entity['reply_to_id'] = reply_to_id
#     entity['reply_to_name'] = reply_to_name
#     entity['context'] = context
#     entity['context_hashtags'] = context_hashtags
#     entity['reply_id'] = reply_id
#     entity['reply_user_id'] = reply_user_id
#     entity['reply_user_name'] = reply_user_name
#     entity['text'] = text
#     client.put(entity)
#     print('Saved', entity.key.name, entity)
