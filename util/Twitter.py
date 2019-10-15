from TwitterAPI import TwitterAPI

access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'


def initApiObject():
    
    #user authentication
    api = TwitterAPI(consumer_key, consumer_secret, access_token, access_token_secret)    
    
    return api				
 
def processDirectMessageEvent(eventObj):
    
    messageText = eventObj.get('message_data').get('text')
    userID = eventObj.get('sender_id')

    twitterAPI = initApiObject()
            
    messageReplyJson = '{"event":{"type":"message_create","message_create":{"target":{"recipient_id":"' + userID + '"},"message_data":{"text":"Hello World!"}}}}'
        
    #ignore casing
    if(messageText.lower() == 'hello bot'):
            
        r = twitterAPI.request('direct_messages/events/new', messageReplyJson)
          
    return None      

def processLikeEvent(eventObj):
    userHandle = eventObj.get('user', {}).get('screen_name')
    
    print ('This user liked one of your tweets: %s' % userHandle) 
    
    return None           
