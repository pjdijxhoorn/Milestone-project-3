import os
from flask import Flask, render_template
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/recipe")
def recipe():
    return render_template("recipe.html")


@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/login")
def login():
    return render_template("login.html")    



if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT")),
        debug=True)