from os import getenv
import traceback
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

db = db_connection.cursor(buffered=True)

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
    flash("Success", "success")
    flash("message", "message")
    flash("ERROR", "error")
    flash("flash")
    return render_template("index.html", title="Mobinfo")


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

        # credentials validation

        if len(user_name) < 4 or (" " in user_name):  # TODO: Also check for special chars
            flash("Username can't be of less than 4 characters or have spaces", "error")
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
                   (user_name, f_name, l_name,
                    generate_password_hash(password), False)
                   )
        db_connection.commit()

        signin_user(session=session, user_name=user_name, first_name=f_name,
                    last_name=l_name, is_admin=False)
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

        signin_user(
            session=session, user_name=user_row[0], first_name=user_row[1], last_name=user_row[2], is_admin=user_row[4])
        flash("Successfully signed in", "success")
        return redirect("/")


@app.route("/signout")
def signout():
    signout_user(session=session)
    flash("Successfully signed out", "success")
    return redirect("/")


@app.route("/brands")
def brands():
    db.execute(f"""
    SELECT name, logo_url FROM brand
    ORDER BY name;
    """)
    db_result = db.fetchall()

    brands = []
    for row in db_result:
        brands.append({"name": row[0], "logo_url": row[1]})

    return render_template("brands.html", brands=brands, title="Brands")


@app.route("/brands/add", methods=["GET", "POST"])
def add_brand():
    if request.method == "GET":
        return render_template("add_brand.html", title="Add Brand")

    else:  # request method is post
        brand_name = request.form.get("brand_name")
        brand_description = request.form.get("brand_description")  # or ""
        brand_logo_url = request.form.get("brand_logo_url")  # or ""
        if not brand_name:
            flash("Can't leave brand name empty.", "error")
            return redirect("/brands/add")

        db.execute("""
        SELECT * FROM brand WHERE name = %s""",
            (brand_name, ))
        if db.fetchone():
            flash("The brand you entered already exists", "error")
            return redirect("/brands")

        db.execute("""
        INSERT INTO brand (name, description, logo_url)
        VALUES (%s, %s, %s);""",
        (brand_name, brand_description, brand_logo_url)
        )
        db_connection.commit()
        flash("Successfully added brand", "success")
        return redirect("/brands")


@ app.route("/brands/<brand_name>")
def brand_details(brand_name):
    # db_result = get_brand_details(brand_name)
    db.execute(f"""
    SELECT name, logo_url, description FROM brand
    WHERE name = %s;
    """, (brand_name, ))
    db_result = db.fetchone()
    if not db_result:
        return "Brand not found."

    return render_template("brand_details.html", brand_name=db_result[0], brand_logo_url=db_result[1], brand_description=db_result[2])


@app.route("/brands/<brand_name>/edit", methods=["POST", "GET"])
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
        brand_description = request.form.get("brand_description")  # or ""
        brand_logo_url = request.form.get("brand_logo_url")  # or ""
        db.execute("""
        UPDATE brand
        SET description = %s, logo_url = %s
        WHERE name = %s;
        """, (brand_description, brand_logo_url, brand_name))
        db_connection.commit()
        flash("Data successfully updated", "success")
        return redirect(f"/brands/{brand_name}")


@app.route("/phones")
def phones():
    db.execute(f"""
    SELECT brand_name, name, image_url, id FROM phone
    ORDER BY name;
    """)
    db_result = db.fetchall()
    phones = []
    for row in db_result:
        phones.append(
            {"brand_name": row[0], "name": row[1], "image_url": row[2], "id": row[3]})

    return render_template("phones.html", phones=phones, title="Phones")


@app.route("/phones/add", methods=["POST", "GET"])
def add_phone():
    if request.method == "GET":
        return render_template("add_phone.html", title="Add Phone")

    else:  # request method is POST
        try:
            brand_name = request.form.get("brand_name").strip()
            phone_name = request.form.get("phone_name").strip()  # or ""
            if (not phone_name) or (not brand_name):
                flash("Please fill all the required fields (marked with *)")
                return redirect(f"/phones/add")
            db.execute("""
            SELECT * FROM brand WHERE name = %s""",
            (brand_name, ))
            if not db.fetchone():
                flash("The brand you entered does not exist. Go to brands page and click Add Brand to add a new brand.", "error")
                return redirect(f"/phones/add")
            image_url = request.form.get("image_url").strip()  # or ""
            os = request.form.get("os").strip()
            weight_grams = int(request.form.get("weight_grams").strip())
            cpu = request.form.get("cpu").strip()
            chipset = request.form.get("chipset").strip()
            display_technology = request.form.get("display_technology").strip()
            screen_size_inches = float(request.form.get("screen_size_inches").strip())
            display_resolution = request.form.get("display_resolution").strip()
            extra_display_features = request.form.get("extra_display_features").strip()
            built_in_memory_gb = int(request.form.get("built_in_memory_gb").strip())
            ram_gb = int(request.form.get("ram_gb").strip())
            front_cameras = [int(mp) for mp in eval(
                request.form.get("front_cameras"))]
            rear_cameras = [int(mp) for mp in eval(
                request.form.get("rear_cameras"))]
            sensors = eval(request.form.get("sensors"))
            colors = eval(request.form.get("colors"))
            battery_capacity_mah = int(
                request.form.get("battery_capacity_mah").strip())
            price_rupees = int(request.form.get("price_rupees").strip())
        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error getting form data. Please try again", "error")
            return redirect(f"/phones/add")

        db.execute("""
        INSERT INTO phone (brand_name, name, image_url, os, weight_grams, cpu, chipset, display_technology, screen_size_inches,
        display_resolution, extra_display_features, built_in_memory_GB, ram_GB, battery_capacity_mah, price_rupees)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
                (brand_name, phone_name, image_url, os, weight_grams, cpu, chipset, display_technology, screen_size_inches, 
        display_resolution, extra_display_features, built_in_memory_gb, ram_gb, battery_capacity_mah, price_rupees)
        )
        db_connection.commit()
        flash("Successfully added to phone table", "success")
        
        # get id of the new phone from database
        db.execute("""
            SELECT id FROM phone
            WHERE brand_name = %s AND name = %s;
            """, (brand_name, phone_name)
        )
        phone_id = db.fetchone()[0]

        # Colors
        for color in colors:
            db.execute("""
            SELECT id FROM color
            WHERE color_name = %s;
            """, (color, ))
            result = db.fetchone()

            if not result:
                # insert color
                db.execute("""
                INSERT INTO color (color_name)
                VALUES (%s);
                """,
                           (color, )
                           )
                db_connection.commit()

                # get color id from database
                db.execute("""
                SELECT id FROM color
                WHERE color_name = %s;
                """, (color, ))
                result = db.fetchone()

            color_id = result[0]

            # insert into phone_color
            db.execute("""
                INSERT INTO phone_color
                (phone_id, color_id)
                VALUES (%s, %s);
                """,
                       (phone_id, color_id)
                       )
            db_connection.commit()
        flash("Successfully added all colors", "success")

        # Sensors
        for sensor in sensors:
            db.execute("""
                SELECT id FROM sensor
                WHERE sensor_name = %s;
                """, (sensor, ))
            result = db.fetchone()

            if not result:
                # insert sensor
                db.execute("""
                INSERT INTO sensor (sensor_name)
                VALUES (%s);
                """,
                           (sensor, )
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM sensor
                WHERE sensor_name = %s;
                """, (sensor, ))
                result = db.fetchone()

            sensor_id = result[0]

            # insert into phone_sensor
            db.execute("""
                INSERT INTO phone_sensor (phone_id, sensor_id)
                VALUES (%s, %s);
                """,
                       (phone_id, sensor_id)
                       )
            db_connection.commit()
        flash("Successfully added all sensors", "success")

        # Cameras
        for camera_mp in rear_cameras:
            # Check if camera exists, if not insert it
            db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "rear"))
            result = db.fetchone()

            if not result:
                # insert rear camera
                db.execute("""
                INSERT INTO camera (megapixels, location)
                VALUES (%s, %s);
                """,
                           (camera_mp, "rear")
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "rear"))
                result = db.fetchone()

            camera_id = result[0]

            # insert into phone_camera
            db.execute("""
                INSERT INTO phone_camera (phone_id, camera_id)
                VALUES (%s, %s);
                """,
                       (phone_id, camera_id)
                       )
            db_connection.commit()
        flash("Successfully added all rear cameras", "success")

        for camera_mp in front_cameras:
            print(camera_mp)
            # Check if camera exists, if not insert it
            db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "front"))
            result = db.fetchone()

            if not result:
                # insert front camera
                db.execute("""
                INSERT INTO camera (megapixels, location)
                VALUES (%s, %s);
                """,
                           (camera_mp, "front")
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "front"))
                result = db.fetchone()

            camera_id = result[0]

            # insert into phone_camera
            db.execute("""
                INSERT INTO phone_camera (phone_id, camera_id)
                VALUES (%s, %s);
                """,
                       (phone_id, camera_id)
                       )
            db_connection.commit()
        flash("Successfully added all front cameras", "success")

        flash("Successfully added all data for new phoe", "success")
        return redirect(f"/phones")


@app.route("/phones/<brand_phone_id>")
def phone_details(brand_phone_id):
    phone_id = int(brand_phone_id[brand_phone_id.find("-") + 1:])

    db.execute("""
    SELECT * FROM phone
    WHERE id = %s;
    """,
               (phone_id,))
    phone_row = db.fetchone()
    if not phone_row:
        return "<h2> Phone not found </h2>"

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
        "ram_gb": phone_row[13],
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
    phone_details["rear_cameras"] = [row[0]
                                     for row in camera_rows if row[1] == "rear"]
    phone_details["front_cameras"] = [row[0]
                                      for row in camera_rows if row[1] == "front"]

    return render_template("phone_details.html", title=f"Specicifications - {phone_details['brand_name']} {phone_details['phone_name']}", phone_details=phone_details)


@app.route("/phones/<brand_phone_id>/edit", methods=["POST", "GET"])
def edit_phone(brand_phone_id):
    # TODO: protect against bogus link (invalid format)
    phone_id = int(brand_phone_id[brand_phone_id.find("-") + 1:])
    # TODO: Also get phone name and brand name and check them while fetching from db
    if request.method == "GET":
        db.execute("""
        SELECT * FROM phone
        WHERE id = %s;
        """, (phone_id, ))
        phone_row = db.fetchone()
        if not phone_row:
            return "<h2> Phone not found </h2>"

        # TODO: DRY! (did following stuff in phones func too)
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
            "ram_gb": phone_row[13],
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
        phone_details["rear_cameras"] = [row[0]
                                         for row in camera_rows if row[1] == "rear"]
        phone_details["front_cameras"] = [row[0]
                                          for row in camera_rows if row[1] == "front"]

        return render_template("edit_phone.html", title=f"Edit - {phone_details['brand_name']} {phone_details['phone_name']}", phone_details=phone_details)

    else:  # method == POST
        try:
            phone_name = request.form.get("phone_name").strip()  # or ""
            if not phone_name:
                flash("Please fill all the required fields (marked with *)")
                return redirect(f"/phones/{brand_phone_id}/edit")
            image_url = request.form.get("image_url").strip()  # or ""
            os = request.form.get("os").strip()
            weight_grams = int(request.form.get("weight_grams").strip())
            cpu = request.form.get("cpu").strip()
            chipset = request.form.get("chipset").strip()
            display_technology = request.form.get("display_technology").strip()
            screen_size_inches = float(request.form.get("screen_size_inches").strip())
            display_resolution = request.form.get("display_resolution").strip()
            extra_display_features = request.form.get("extra_display_features").strip()
            built_in_memory_gb = int(request.form.get("built_in_memory_gb").strip())
            ram_gb = int(request.form.get("ram_gb").strip())
            front_cameras = [int(mp) for mp in eval(
                request.form.get("front_cameras"))]
            rear_cameras = [int(mp) for mp in eval(
                request.form.get("rear_cameras"))]
            # front_cameras = eval(request.form.get("front_cameras"))
            # rear_cameras = eval(request.form.get("rear_cameras"))
            sensors = eval(request.form.get("sensors"))
            colors = eval(request.form.get("colors"))
            battery_capacity_mah = int(
                request.form.get("battery_capacity_mah").strip())
            price_rupees = int(request.form.get("price_rupees").strip())
        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error getting form data. Please try again", "error")
            return redirect(f"/phones/{brand_phone_id}/edit")

        db.execute("""
        UPDATE phone
        SET name = %s, image_url = %s, os = %s, weight_grams = %s, cpu = %s, chipset = %s, display_technology = %s, screen_size_inches = %s, display_resolution = %s, extra_display_features = %s, built_in_memory_GB = %s, ram_GB = %s, battery_capacity_mah = %s, price_rupees = %s
        WHERE id = %s;
        """,
                   (phone_name, image_url, os, weight_grams, cpu, chipset, display_technology, screen_size_inches,
                    display_resolution, extra_display_features, built_in_memory_gb, ram_gb, battery_capacity_mah, price_rupees, phone_id)
                   )
        db_connection.commit()

        # Colors
        # Delete existing colors for the current phone
        db.execute("""
        DELETE FROM phone_color
        WHERE phone_id = %s;""",
                   (phone_id, ))
        for color in colors:
            db.execute("""
            SELECT id FROM color
            WHERE color_name = %s;
            """, (color, ))
            result = db.fetchone()

            if not result:
                # insert color
                db.execute("""
                INSERT INTO color (color_name)
                VALUES (%s);
                """,
                           (color, )
                           )
                db_connection.commit()

                # get color id from database
                db.execute("""
                SELECT id FROM color
                WHERE color_name = %s;
                """, (color, ))
                result = db.fetchone()

            color_id = result[0]

            # insert into phone_color
            db.execute("""
                INSERT INTO phone_color
                (phone_id, color_id)
                VALUES (%s, %s);
                """,
                       (phone_id, color_id)
                       )
            db_connection.commit()

        # Sensors
        # Delete existing sensors for the current phone
        db.execute("""
        DELETE FROM phone_sensor
        WHERE phone_id = %s;""",
                   (phone_id, ))
        for sensor in sensors:
            db.execute("""
                SELECT id FROM sensor
                WHERE sensor_name = %s;
                """, (sensor, ))
            result = db.fetchone()

            if not result:
                # insert sensor
                db.execute("""
                INSERT INTO sensor (sensor_name)
                VALUES (%s);
                """,
                           (sensor, )
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM sensor
                WHERE sensor_name = %s;
                """, (sensor, ))
                result = db.fetchone()

            sensor_id = result[0]

            # insert into phone_sensor
            db.execute("""
                INSERT INTO phone_sensor (phone_id, sensor_id)
                VALUES (%s, %s);
                """,
                       (phone_id, sensor_id)
                       )
            db_connection.commit()

        # Cameras
        # Delete existing cameras for the current phone
        db.execute("""
        DELETE FROM phone_camera
        WHERE phone_id = %s;""",
                   (phone_id, ))
        for camera_mp in rear_cameras:
            # Check if camera exists, if not insert it
            db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "rear"))
            result = db.fetchone()

            if not result:
                # insert rear camera
                db.execute("""
                INSERT INTO camera (megapixels, location)
                VALUES (%s, %s);
                """,
                           (camera_mp, "rear")
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "rear"))
                result = db.fetchone()

            camera_id = result[0]

            # insert into phone_camera
            db.execute("""
                INSERT INTO phone_camera (phone_id, camera_id)
                VALUES (%s, %s);
                """,
                       (phone_id, camera_id)
                       )
            db_connection.commit()

        for camera_mp in front_cameras:
            print(camera_mp)
            # Check if camera exists, if not insert it
            db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "front"))
            result = db.fetchone()

            if not result:
                # insert front camera
                db.execute("""
                INSERT INTO camera (megapixels, location)
                VALUES (%s, %s);
                """,
                           (camera_mp, "front")
                           )
                db_connection.commit()

                db.execute("""
                SELECT id FROM camera
                WHERE megapixels = %s and location = %s;
                """, (camera_mp, "front"))
                result = db.fetchone()

            camera_id = result[0]

            # insert into phone_camera
            db.execute("""
                INSERT INTO phone_camera (phone_id, camera_id)
                VALUES (%s, %s);
                """,
                       (phone_id, camera_id)
                       )
            db_connection.commit()

        flash("Successfully updated data", "success")
        return redirect(f"/phones/{brand_phone_id}")

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html', pic=pic), 404


app.run(debug=True)
