from flask import Flask, render_template, request
from os import getenv
import mysql.connector
from mysql.connector.constants import RefreshOption
from werkzeug.utils import redirect


db_connection = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = getenv("MySQLpassword"),
    database = "mobinfo"
)

db = db_connection.cursor()

app = Flask(__name__)
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)



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
    db.execute(f"""
    SELECT name, logo_url FROM brand
    ORDER BY name;
    """)
    db_result = db.fetchall()

    brands = []
    for row in db_result:
        brands.append({"name": row[0], "logo_url": row[1]})

    return render_template("brands.html", brands=brands)


@app.route("/brands/<brand_name>")
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
        brand_name = request.form.get("brand_name") #or ""
        brand_description = request.form.get("brand_description") #or ""
        brand_logo_url = request.form.get("brand_logo_url") #or ""
        db.execute("""
        UPDATE brand
        SET name = %s, description = %s, logo_url = %s
        WHERE name = %s;
        """, (brand_name, brand_description, brand_logo_url, brand_name))
        db_connection.commit()
        return redirect(f"/brands/{brand_name}")

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html', pic=pic), 404

    