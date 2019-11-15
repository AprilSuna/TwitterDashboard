from google.cloud import datastore
import pandas as pd
datastore_client = datastore.Client('twitterdashboard')

# for each user, get data from datastore
def get_data(client, kind):
    query = client.query(kind = kind)
    query.projection = ['reply_to_name', 'reply_user_id', 'toxicity', 'threat',\
    'sexually_explicit', 'flirtation', 'identity_attack', 'insult', 'profanity']
    reply_to_name = []
    reply_user_id = []
    toxicity = []
    threat = []
    sexually_explicit = []
    flirtation = []
    identity_attack = []
    insult = []
    profanity = []
    for result in query.fetch():
        if not result['reply_user_id']:
            continue
        else:
            reply_to_name.append(result['reply_to_name'])
            reply_user_id.append(result['reply_user_id'])
            toxicity.append(result['toxicity'])
            threat.append(result['threat'])
            sexually_explicit.append(result['sexually_explicit'])
            flirtation.append(result['flirtation'])
            identity_attack.append(result['identity_attack'])
            insult.append(result['insult'])
            profanity.append(result['profanity'])
    
    df = pd.DataFrame(list(zip(reply_to_name, reply_user_id, toxicity, threat, sexually_explicit, flirtation, identity_attack, insult, profanity)), 
    columns =query.projection)
    print(df)
