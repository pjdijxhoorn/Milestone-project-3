import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__, template_folder="templates", static_folder="static")


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.route("/")
def index():
    newRecipies = mongo.db.recipies.find().sort('_id', -1).limit(3)
    return render_template("index.html", newRecipies=newRecipies)


@app.route("/recipe")
def recipe():
    recipies = mongo.db.recipies.find()
    # this code checks for a loggedin user and displays his fav recipes
    try:
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]

        user = mongo.db.users.find_one({"username": session["user"]})
        try:
            favourites = user.get("favourites")
        except:
            favourites = []
    except:
        favourites = []
        username = []
    return render_template(
        "recipe.html", recipies=recipies, favourites=favourites,
        username=username)


@app.route("/search", methods=["GET", "POST"])
def search():
    try:
        # this code checks for a logged in user and displays his fav recipes
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]

        user = mongo.db.users.find_one({"username": session["user"]})
        try:
            favourites = user.get("favourites")
        except:
            favourites = []
    except:
        favourites = []
        username = []

    # this code searches the recipes trough the search field
    query = request.form.get("query")
    recipies = list(mongo.db.recipies.find({"$text": {"$search": query}}))
    if recipies == []:
        flash("Sorry we couldn't find anything matching Your search query!")
    return render_template(
        "recipe.html", recipies=recipies, favourites=favourites)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # check if email already exists in db
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})

        password = request.form.get("password")
        passwordconfirm = request.form.get("passwordconfirm")
        # check for existing users / mail and password confirm
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if existing_email:
            flash("Email is already registered")
            return redirect(url_for("register"))

        if password != passwordconfirm:
            flash("The passwords should match")
            return redirect(url_for("register"))

        # build a new user
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get(
                "passwordconfirm")),
            "email": request.form.get("email"),
            "favourites": [""]
        }
        mongo.db.users.insert_one(register)

        # welcome message
        welcome = {
            "created_by": "admin",
            "for": request.form.get("username").lower(),
            "messages": ("Welcome to the site!")}
        # send message
        mongo.db.messages.insert_one(welcome)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # does password match user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    if request.method == "POST":
        # checks if the user exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("for").lower()})

        if existing_user:
            # content message
            message = {
                "created_by": session["user"],
                "for": request.form.get("for"),
                "messages": request.form.get("mail")}
            # send message
            mongo.db.messages.insert_one(message)
            flash("Message send")

        else:
            flash("no such user")
        return redirect(url_for("profile", username=session["user"]))
    # finds the user his messages and his recipies
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    userRecipe = mongo.db.recipies.find(
        {"created_by": session["user"]})
    messages = mongo.db.messages.find(
        {"for": session["user"]})
    # finds the favourite recipes
    try:
        user = mongo.db.users.find_one({"username": session["user"]})
        try:
            favourites = user.get("favourites")
        except:
            favourites = []

    except:
        favourites = []
        username = []

    recipies = mongo.db.recipies.find()
    users = mongo.db.users.find()
    if session["user"]:
        return render_template(
            "profile.html", username=username, userRecipe=userRecipe,
            messages=messages, recipies=recipies, favourites=favourites,
            users=users)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/addRecipies", methods=["GET", "POST"])
def addRecipies():
    if request.method == "POST":
        # gets all the info from the form and creates a recipe
        recipe = {
            "category_name": request.form.get("category_name"),
            "Name_dish": request.form.get("Name_dish"),
            "preperation_time": request.form.get("preperation_time"),
            "Photo_link": request.form.get("Photo_link"),
            "ingredients": request.form.get("ingredients"),
            "explanation": request.form.get("explanation"),
            "Other_requirments": request.form.get("Other_requirments"),
            "created_by": session["user"]
        }
        # inserts the recipe
        mongo.db.recipies.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("addRecipies"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("addRecipies.html", categories=categories)


@app.route("/editRecipe/<recipe_id>", methods=["GET", "POST"])
def editRecipe(recipe_id):
    if request.method == "POST":
        # gets a recipe and takes all info /changes from the form and saves it
        editedRecipe = {
            "category_name": request.form.get("category_name"),
            "Name_dish": request.form.get("Name_dish"),
            "preperation_time": request.form.get("preperation_time"),
            "Photo_link": request.form.get("Photo_link"),
            "ingredients": request.form.get("ingredients"),
            "explanation": request.form.get("explanation"),
            "Other_requirments": request.form.get("Other_requirments"),
            "created_by": session["user"]
        }
        mongo.db.recipies.update({"_id": ObjectId(recipe_id)}, editedRecipe)
        flash("Recipe Successfully saved")

    recipe = mongo.db.recipies.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
        "editRecipe.html", recipe=recipe, categories=categories)


@app.route("/deleteRecipe/<recipe_id>", methods=["GET", "POST"])
def deleteRecipe(recipe_id):
        # deletes recipe
        mongo.db.recipies.remove({"_id": ObjectId(recipe_id)})
        flash("recipe succesfully deleted")
        return redirect(url_for('profile', username=session['user']))


@app.route("/adminpage")
def adminpage():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("adminpage.html", categories=categories)


@app.route("/addCategory", methods=["GET", "POST"])
def addCategory():
    # gets info from form and adds that to catogories
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New category Added")
        return redirect(url_for("adminpage"))
    return render_template("addCategory.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    # if submitted change the catogory to input from form
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("adminpage"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    # delete catogory
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("adminpage"))


@app.route("/deletemessage/<message_id>", methods=["GET", "POST"])
def deletemessage(message_id):
    # delete message
    mongo.db.messages.remove({"_id": ObjectId(message_id)})
    flash("message successfully deleted")
    return redirect(url_for('profile', username=session['user']))


@app.route("/singleRecipe/<recipe_id>", methods=["GET", "POST"])
def singleRecipe(recipe_id):
    # shows recipe that is clicked from recipe card as single recipe
    recipies = mongo.db.recipies.find({"_id": ObjectId(recipe_id)})
    return render_template("singleRecipe.html", recipies=recipies)


@app.route("/favourite/<recipe_id>", methods=["GET", "POST"])
def favourite(recipe_id):

    # get recipe id and user
    recipe = mongo.db.recipies.find(
        {"_id": ObjectId(recipe_id)})
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user = mongo.db.users.find_one(
        {"username": session["user"], "favourites": recipe_id})

    # check users favourites if no one logged in then empty favourites
    try:
        favourites = user.get("favourites")
    except:
        favourites = []

    # if the recipe favourite icon is clicked toggle
    # add/remove recipe to array favourites
    if recipe_id in favourites:
        mongo.db.users.update(
            {"username": session["user"]},
            {"$pull": {"favourites": recipe_id}})
    else:
        mongo.db.users.update_one(
            {"username": session["user"]},
            {"$push": {"favourites": recipe_id}})
    return redirect(url_for(
        "recipe", recipe=recipe, username=username, favourites=favourites))


@app.route("/favourites/<recipe_id>", methods=["GET", "POST"])
def favourites(recipe_id):
    recipe = mongo.db.recipies.find(
        {"_id": ObjectId(recipe_id)})
    # same function as above only for profile page redirect
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    user = mongo.db.users.find_one(
        {"username": session["user"], "favourites": recipe_id})
    try:
        favourites = user.get("favourites")
    except:
        favourites = []

    if recipe_id in favourites:
        mongo.db.users.update(
            {"username": session["user"]},
            {"$pull": {"favourites": recipe_id}})
    else:
        mongo.db.users.update_one(
            {"username": session["user"]},
            {"$push": {"favourites": recipe_id}})
    return redirect(url_for("profile",
                    recipe=recipe, username=username, favourites=favourites))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT")),
        debug=True)

    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT")),
        debug=True)
