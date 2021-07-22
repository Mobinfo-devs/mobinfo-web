def signin_user(session, user_name, first_name, last_name, is_admin):
    session["user_name"] = user_name
    session["first_name"] = first_name
    session["last_name"] = last_name
    session["is_admin"] = is_admin

def signout_user(session):
    session.clear()