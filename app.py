from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", title="Mobinfo")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", title="Sign Up")
    else:  # sign up form submitted
        pass
        # TODO: Write signup logic


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html", title="Sign In")
    else:  # sign in form submitted
        pass
        # TODO: Write signup logic


@app.route("/brands")
def brands():
    return render_template("brands.html")


app.run(debug=True)
