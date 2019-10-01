from google.cloud import datastore


def alreadyExist(username):
    datastore_client = datastore.Client('twitterdashboard')
    key = datastore_client.key('Userfile', username)
    if not key:
        return False
    else:
        return True
