from flask import Flask, render_template
app = Flask(__name__)

print("running")


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(ssl_context=('/etc/letsencrypt/live/test.theofficialjosh.com/fullchain.pem', '/etc/letsencrypt/live/test.theofficialjosh.com/privkey.pem'))


