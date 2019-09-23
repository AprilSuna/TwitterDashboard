from flask import *

app = Flask(__name__)

@app.route("/login",methods=['POST','GET'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin123':
            error= "sorry"
        else:
            return redirect(url_for('index'))
    return render_template('login.html',error=error)

@app.route('/')
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8080, debug=True)
