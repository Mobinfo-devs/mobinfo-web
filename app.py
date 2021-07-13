from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/signup")
def signup():
    if request.args.get("name"):
        print(request.args.get("name"))
    return render_template("signup.html")



app.run(debug=True)