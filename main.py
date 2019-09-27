from flask import Flask, session, redirect, request, render_template
import tweepy
# from flask_session import Session

app = Flask(__name__)
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SECRET_KEY'] = 'redsfsfsfsfis'
# sess = Session()
# sess.init_app(app)

# april's tokens
# access_token = '1106277569752633351-z9XGTbAL7ZxEqT7aToonp8NvO4XuQJ'
# access_token_secret = 'EEKofWc9VV0a4V16wtdAoPSvZHbhZtriyZgKZTf20M7Bq'
# consumer_key = '8lkEPXD9VBXwNxES21RR8k0vZ'
# consumer_secret = 'hkLL9WWMnhbz7trMlfIOgzyctXayT1ZzUYilmdWi16xEhJs4FM'

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'

callback_uri = 'https://twitterdashboard.appspot.com/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'

@app.route('/',methods=['POST','GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)

@app.route("/login",methods=['POST','GET'])
def login():
    error = None
    # if request.method == 'POST':
    #     if request.form['username'] != 'admin' or request.form['password'] != 'admin123':
    #         error= "sorry"
    #     else:
    #         return redirect(url_for('index'))
    return render_template('login.html',error=error)

@app.route("/register",methods=['POST','GET'])
def register():
    if request.method == 'POST':
        # get username and password from request.form
        # save to our database, it's the login info for our service
        username = request.form.get('username')
        password = request.form.get('password')
        print('username:', username)
        print('password:', password)
        return redirect('/auth')
    return render_template('register.html')
    
@app.route("/auth",methods=['POST','GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()
    # print(redirect_url)
    # print(auth.request_token)
    session['request_token'] = auth.request_token
    return redirect(redirect_url)

@app.route("/callback",methods=['POST','GET'])
def callback():
    request_token = session['request_token']
    del session['request_token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    print(verifier)
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    print(auth.access_token, auth.access_token_secret)
    # return redirect(url_for("index"))
    return redirect('/app')

@app.route('/app')
def get_tweets():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    tweets = api.user_timeline(screen_name=username)                                                                            
    print([{'tweet': t.text,
              'created_at': t.created_at, 
              'username': username,
              'headshot_url': t.user.profile_image_url}
           for t in tweets])
    return render_template('app.html')



if __name__ == '__main__':
    # app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'
    app.run(host='127.0.0.1',port=8080, debug=True)
