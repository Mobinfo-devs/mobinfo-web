from os import getenv

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helper import signin_user, signout_user

db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=getenv("MySQLpassword"),
    database="mobinfo"
)

db = db_connection.cursor()

app = Flask(__name__)
app.secret_key = "35gbbad932565nnssndg"
# app.config.update(
#     DEBUG=True,
#     TEMPLATES_AUTO_RELOAD=True
# )
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    # flash("Success", "success")
    # flash("message", "message")
    # flash("ERROR", "error")
    # flash("flash")
    return render_template("index.html", title="Mobinfo", error="sup")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", title="Sign Up")
    else:  # sign up form submitted
        f_name = request.form.get("firstname").strip()
        l_name = request.form.get("lastname").strip()
        user_name = request.form.get("username").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirmpassword")

        ## credentials validation

        if len(user_name) < 4 or (" " in user_name):  # TODO: Also check for special chars
            flash("Username can't be of less than 4 characters", "error")
            return render_template("signup.html", title="Sign Up")
        
        # checking if username already exists
        db.execute("""
        SELECT * FROM user
        WHERE username = %s;""",
                   (user_name,)
                   )
        if db.fetchone():  # if row exists where username is present
            flash("Sorry, that username already exists", "error")
            return render_template("signup.html", title="Sign Up")

        if len(password) < 6:
            flash("Password must be atleast 6 characters.", "error")
            return render_template("signup.html", "Sign Up")

        # checking if both passwords match
        if password != confirm_password:
            flash("Passwords don't match", "error")
            return render_template("signup.html", title="signup")
        

        db.execute("""
        INSERT INTO user (username, firstname, lastname, password_hash, is_admin)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (user_name, f_name, l_name, generate_password_hash(password), False)
        )
        db_connection.commit()

        signin_user(user_name=user_name, first_name=f_name, last_name=l_name, is_admin=False)
        flash("Successfully registered and logged in.", "success")
        return redirect("/")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html", title="Sign In")
    else:  # sign in form submitted
        user_name = request.form.get("username").strip()
        password = request.form.get("password")
        print(user_name)
        # checking if user exists
        db.execute("""
        SELECT * FROM user
        WHERE username = %s;""",
                   (user_name,)
                   )
        user_row = db.fetchone()
        print(user_row)
        if not user_row:  # if row exists where username is present
            flash("Invalid username", "error")
            return render_template("signin.html", title="Sign In")

        # Checking if password is valid
        if not check_password_hash(user_row[3], password):
            flash("Incorrect password", "error")
            return render_template("signin.html", title="Sign In")
        
        signin_user(session=session, user_name=user_row[0], first_name=user_row[1], last_name=user_row[2], is_admin=user_row[4])
        flash("Successfully signed in", "success")
        return redirect("/")


@app.route("/signout")
def signout():
    signout_user(session=session)
    flash("Successfully signed out", "success")
    return redirect("/")
    
@ app.route("/brands")
def brands():
    db.execute(f"""
    SELECT name, logo_url FROM brand
    ORDER BY name;
    """)
    db_result = db.fetchall()

    brands = []
    for row in db_result:
        brands.append({"name": row[0], "logo_url": row[1]})

    return render_template("brands.html", brands=brands)


@ app.route("/brands/<brand_name>")
def specific_brand(brand_name):
    # db_result = get_brand_details(brand_name)
    db.execute(f"""
    SELECT name, logo_url, description FROM brand
    WHERE name = %s;
    """, (brand_name, ))
    db_result = db.fetchone()
    if not db_result:
        return "Brand not found."

    return render_template("brand_detail.html", brand_name=db_result[0], brand_logo_url=db_result[1], brand_description=db_result[2])


@ app.route("/brands/<brand_name>/edit", methods=["POST", "GET"])
def edit_brand(brand_name):
    if request.method == "GET":
        db.execute(f"""
        SELECT name, logo_url, description FROM brand
        WHERE name = %s;
        """, (brand_name, ))
        db_result = db.fetchone()
        if not db_result:
            return "Brand not found!"

        return render_template("edit_brand.html", brand_name=db_result[0], brand_logo_url=db_result[1], brand_description=db_result[2])

    else:  # method == POST
        brand_name = request.form.get("brand_name")  # or ""
        brand_description = request.form.get("brand_description")  # or ""
        brand_logo_url = request.form.get("brand_logo_url")  # or ""
        db.execute("""
        UPDATE brand
        SET name = %s, description = %s, logo_url = %s
        WHERE name = %s;
        """, (brand_name, brand_description, brand_logo_url, brand_name))
        db_connection.commit()
        flash("Data successfully updated", "success")
        return redirect(f"/brands/{brand_name}")

@app.route("/phones")
def phones(): 
    db.execute(f"""
    SELECT brand_name, name, image_url, id FROM phone
    """)
    db_result = db.fetchall()
    phones = []
    for row in db_result:
        phones.append({"brand_name": row[0], "name": row[1], "image_url": row[2], "id": row[3]})

    return render_template("phones.html", phones=phones)


@app.route("/phones/<brand_phone_id>")
def phone_specs(brand_phone_id):
    phone_id = int(brand_phone_id[ brand_phone_id.find("-") + 1 : ])

    db.execute("""
    SELECT * FROM phone
    WHERE id = %s;
    """,
    (phone_id,) )
    phone_row = db.fetchone()
    if not phone_row:
        return "<h2> Phone not found </h2>"
    else:
        phone_details = {
            "id": phone_row[0],
            "brand_name": phone_row[1],
            "phone_name": phone_row[2],
            "image_url": phone_row[3],
            "os": phone_row[4],
            "weight_grams": phone_row[5],
            "cpu": phone_row[6],
            "chipset": phone_row[7],
            "display_technology": phone_row[8],
            "screen_size_inches": phone_row[9],
            "display_resolution": phone_row[10],
            "extra_display_features": phone_row[11],
            "built_in_memory_gb": phone_row[12],
            "ram_GB": phone_row[13],
            "battery_capacity_mah": phone_row[14],
            "price_rupees": phone_row[15]
        }

    # get colors
    db.execute("""
    SELECT color.color_name
    FROM color INNER JOIN phone_color
    ON color.id = phone_color.color_id
    WHERE phone_color.phone_id = %s
    """,
    (phone_id, ))
    phone_details["colors"] = [row[0] for row in db.fetchall()]

    # get sensors
    db.execute("""
    SELECT sensor.sensor_name
    FROM sensor INNER JOIN phone_sensor
    ON sensor.id = phone_sensor.sensor_id
    WHERE phone_sensor.phone_id = %s
    """,
    (phone_id, ))
    phone_details["sensors"] = [row[0] for row in db.fetchall()]

    # get cameras
    db.execute("""
    SELECT camera.megapixels, camera.location
    FROM camera INNER JOIN phone_camera
    ON camera.id = phone_camera.camera_id
    WHERE phone_camera.phone_id = %s
    """,
    (phone_id, ))
    camera_rows = db.fetchall()
    phone_details["rear_cameras"] = [row[0] for row in camera_rows if row[1] == "rear"]
    phone_details["front_cameras"] = [row[0] for row in camera_rows if row[1] == "front"]

    return render_template("specs.html", title=f"Specicifications - {phone_details['brand_name']} {phone_details['phone_name']}", phone_details=phone_details)

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html', pic=pic), 404


app.run(debug=True)
