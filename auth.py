import streamlit as st
import jwt
import datetime
import bcrypt
from db import get_connection

SECRET_KEY = "MY_SECRET_KEY_123456"

def create_token(username):
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["username"]
    except:
        return None

def login_signup_page():

    db = get_connection()
    cursor = db.cursor()

    st.title("🔐 User Login")

    menu = st.sidebar.selectbox("Select Option", ["Login", "Signup"])

    if menu == "Signup":

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Signup"):

            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            cursor.execute(
                "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
                (username, email, hashed_pw)
            )
            db.commit()
            st.success("✅ Signup Successful")

    else:

        user_input = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            cursor.execute(
                "SELECT username,password FROM users WHERE email=%s OR username=%s",
                (user_input, user_input)
            )
            result = cursor.fetchone()

            if result:

                db_username, db_password = result

                if isinstance(db_password, str):
                    db_password = db_password.encode("utf-8")
                elif isinstance(db_password, bytearray):
                    db_password = bytes(db_password)

                if bcrypt.checkpw(password.encode("utf-8"), db_password):

                    token = create_token(db_username)

                    st.session_state.logged_in = True
                    st.session_state.username = db_username
                    st.session_state.token = token
                    st.rerun()
                else:
                    st.error("❌ Invalid Password")
            else:
                st.error("❌ User Not Found")
