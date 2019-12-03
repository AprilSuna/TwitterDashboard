from google.cloud import datastore
import pandas as pd
import collections
from sklearn.linear_model import LogisticRegression
from functions import store_visited_users, get_visited_users, store_data
datastore_client = datastore.Client('twitterdashboard')
indexs = ['reply_to_name', 'reply_user_id', 'toxicity', 'threat', 'sexually_explicit', 'flirtation', 'identity_attack', 'insult', 'profanity']


class LogisticRegressionModel():
    def __init__(self, client, model, indexs):
        self.client = client
        self.model = model
        self.indexs = indexs

    #get each users' kind_id
    def get_all_kinds(self):
        query = self.client.query(kind = 'user')
        query.projection = ['twitter_id']
        kind_ids = []
        for result in query.fetch():
            kind_ids.append(result['twitter_id'])
        print(kind_ids)
        return kind_ids

    #for each user get data from datastore
    def get_user_data(self, kind):
        query = self.client.query(kind = kind)
        query.projections = indexs
        reply_results = []
        for result in query.fetch():
            if 'reply_user_id' not in result:
                continue
            else:
                reply_results.append((result['reply_to_name'], result['reply_user_id'], result['toxicity'], result['threat'], result['sexually_explicit'], result['flirtation'], result['identity_attack'], result['insult'], result['profanity']))
        df = pd.DataFrame(reply_results, columns = self.indexs)
        return df

    #group_by_user
    def group_by_reply_user(self, kind, indexs):
        df = self.get_user_data(kind)
        feature_vector = []
        new_index = indexs[:]
        new_index.remove('reply_to_name')
        new_index.remove('reply_user_id')
        grouped = df.groupby(df['reply_user_id']).mean()
        return grouped

    #get reply user label
    def get_reply_user_label(self, kind, indexs):
        grouped = self.group_by_reply_user(kind, indexs)
        query = self.client.query(kind = 'bm')
        query.projections = ['bm_ids']
        muted_users = collections.defaultdict(list)
        for result in query.fetch():
            key = result.key.id_or_name
            print(result)
            muted_users[key].append(result['bm_ids'])
        users_list = grouped.index.tolist()
        store_visited_users(self.client, kind, users_list)
        print('user list here' + str(users_list))
        muted_or_not = []
        for user in users_list:
            if user in muted_users:
                muted_or_not.append(1)
            else:
                muted_or_not.append(0)
        return muted_or_not

    #def model itself
    def trainingModel(self, kind, indexs):
        X_train = self.group_by_reply_user(kind, indexs).values.tolist()
        y_train = self.get_reply_user_label(kind, indexs)
        print(X_train)
        print(y_train)
        logreg = self.model()
        logreg.fit(X_train, y_train)
        return logreg

    #get new data
    def get_new_data(self, kind):
        visited_users = get_visited_users(self.client, kind)
        users = self.group_by_reply_user(kind, self.indexs).index.tolist()
        new_users = []
        for user in users:
            if user not in visited_users:
                new_users.append(user)
            else:
                continue
        new_data = self.group_by_reply_user(kind, self.indexs).loc[ new_users , : ]
        return (new_data.values.tolist(), new_users)



lgObject = LogisticRegressionModel(datastore_client, LogisticRegression, indexs)
users = lgObject.get_all_kinds()
store_data(datastore_client, '1106277569752633351', [1,1], [u'11111', u'22222'])
for user in users:
    model = lgObject.trainingModel(user, indexs)
    (new_data, new_users) = lgObject.get_new_data(user)
    if len(new_data) != 0:
        predict = model.predict(new_data)
        store_data(datastore_client, user, predict, new_users)
