from google.cloud import datastore

def store_visited_users(client, kind, users_list):
    task_key = client.key('visited', kind) 
    entity = datastore.Entity(key=task_key)
    entity['visited_users'] = users_list
    client.put(entity)
    return

def get_visited_users(client, kind):
    query = client.query(kind  = 'visited')
    query.projection = [str(kind)]
    users = []
    for result in query.fetch():
        users.append(result)
    return users

def store_data(client, kind, result, users):
    bm_list = []
    query = client.query(kind = 'bm')
    query.projections = ['bm_ids']
    for rs in query.fetch():
        if rs.key.id_or_name == kind:
            print(rs['bm_ids'])
            bm_list = rs['bm_ids']
    for i in range(len(result)):
        print(result)
        if result[i] == 1:
            bm_list.append(users[i])
        else:
            continue
    task_key = client.key('bm', kind)
    entity = datastore.Entity(key = task_key)
    print('new list here', bm_list)
    entity['bm_ids'] = bm_list
    client.put(entity)
    return

