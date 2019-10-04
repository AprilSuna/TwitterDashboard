from google.cloud import datastore
from hashlib import pbkdf2_hmac
from random import getrandbits

# datastore_client = datastore.Client('twitterdashboard')

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