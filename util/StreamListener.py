import tweepy


class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        id_str = status.id_str
        text = status.text
        # hashtags = status.entities.hashtags
        # symbols = status.entities.symbols
        # user_mentions = status.entities.user_mentions
        # in_reply_to_screen_name = status.in_reply_to_screen_name
        # in_reply_to_status_id_str = status.in_reply_to_status_id_str
        in_reply_to_user_id_str = status.in_reply_to_user_id_str
        user_id_str = status.user.id_str
        # user_screen_name = status.user.screen_name
        # user_description = status.user.description
        is_reply = False
        if in_reply_to_user_id_str is not None:
            is_reply = True
            print('is_reply')
            # muted_user = api.create_mute(user_id_str)
            print('muted', user_id_str)
        print(id_str, text)