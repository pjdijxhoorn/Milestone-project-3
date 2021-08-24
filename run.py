import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env
 

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
def index():
    newRecipies = mongo.db.recipies.find().sort('_id', -1).limit(3)
    return render_template("index.html", newRecipies = newRecipies )


@app.route("/recipe")
def recipe():
    recipies = mongo.db.recipies.find()

    favourites = mongo.db.favourites.find(
        {"created_by": session["user"]})

    return render_template("recipe.html", recipies = recipies, favourites = favourites)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipies = list(mongo.db.recipies.find({"$text": {"$search": query}}))
    if recipies == []:
        flash("Sorry we couldn't find anything matching Your search query!")
    return render_template("recipe.html", recipies = recipies)


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

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if existing_email:
            flash("Email is already registered")
            return redirect(url_for("register"))

        if password != passwordconfirm:
            flash("The passwords should match")
            return redirect(url_for("register"))


        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("passwordconfirm")),
            "email": request.form.get("email")
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect (url_for("profile", username=session["user"]))

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
                    return redirect (url_for("profile", username=session["user"]))
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
    #grab the session user's username from db
    if request.method == "POST":
        message = {
            "created_by": session["user"],
            "for": request.form.get("for"),
            "messages": request.form.get("mail")}
    
        mongo.db.messages.insert_one(message)
        flash("Message send")
        return redirect (url_for("profile", username=session["user"]))
    
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    
    userRecipe = mongo.db.recipies.find(
        {"created_by": session["user"]})
    
    messages = mongo.db.messages.find(
        {"for": session["user"]})
     
    if session["user"]:
        return render_template("profile.html", username=username, userRecipe=userRecipe, messages=messages)
    return redirect (url_for("login"))

@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect (url_for("login"))


@app.route("/addRecipies", methods=["GET", "POST"])
def addRecipies():
    if request.method == "POST":
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
        mongo.db.recipies.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("addRecipies"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("addRecipies.html", categories=categories)

@app.route("/editRecipe/<recipe_id>", methods=["GET", "POST"])
def editRecipe(recipe_id):
    if request.method == "POST":
        
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
        flash("Recipe Successfully edited")
    
    recipe = mongo.db.recipies.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("editRecipe.html", recipe=recipe, categories=categories)

@app.route("/deleteRecipe/<recipe_id>", methods=["GET", "POST"])
def deleteRecipe(recipe_id):
       mongo.db.recipies.remove({"_id": ObjectId(recipe_id)})
       flash("recipe succesfully deleted")
       return redirect ( url_for('profile', username=session['user']))
   
@app.route("/adminpage")
def adminpage():
    categories = list (mongo.db.categories.find().sort("category_name", 1))
    return render_template("adminpage.html", categories = categories)

@app.route("/addCategory", methods=["GET", "POST"])
def addCategory():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New category Added")
        return redirect(url_for("adminpage"))
    return render_template ("addCategory.html")

@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
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
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("adminpage"))

@app.route("/deletemessage/<message_id>", methods=["GET", "POST"])
def deletemessage(message_id):
    mongo.db.messages.remove({"_id": ObjectId(message_id)})
    flash("message successfully deleted")
    return redirect ( url_for('profile', username=session['user']))

@app.route("/singleRecipe/<recipe_id>", methods=["GET", "POST"])
def singleRecipe(recipe_id):
    recipies = mongo.db.recipies.find({"_id": ObjectId(recipe_id)})
    return render_template("singleRecipe.html", recipies = recipies)

@app.route("/favourite/<recipe_id>", methods=["GET", "POST"])
def favourite(recipe_id):
    recipe = mongo.db.recipies.find(
        {"_id": ObjectId(recipe_id)})

    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    user = mongo.db.users.find_one({"username": session["user"],"favourites": recipe_id})
    try:
        test = user.get("favourites")
    except: 
        test = []
   

    if recipe_id in test:
        print("hello")    
    else:
         mongo.db.users.update_one({"username": session["user"]},{"$push":{"favourites": recipe_id}})
    return redirect (url_for("recipe", recipe = recipe, username = username, ))

if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT")),
        debug=True)