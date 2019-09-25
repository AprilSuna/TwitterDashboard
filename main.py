from flask import *
import tweepy
from flask_session import Session

app = Flask(__name__)
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SECRET_KEY'] = 'redsfsfsfsfis'
# sess = Session()
# sess.init_app(app)



callback_uri = 'https://localhost:8080/callback'
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

        return redirect('/auth')


@app.route("/auth",methods=['POST','GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()
    print(redirect_url)
    print(auth.request_token)
    session['request_token'] = auth.request_token

    return redirect(redirect_url)

@app.route("/callback",methods=['POST','GET'])
def callback():
    request_token = session['request_token']
    del session['request_token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    print(auth.access_token, auth.access_token_secret)

    return redirect('/index')


if __name__ == '__main__':
    app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'
    app.run(host='127.0.0.1',port=8080, debug=True)
