import streamlit as st
import pandas as pd
import bcrypt
from db import get_connection
from auth import verify_token, create_token


def dashboard_page():

    db = get_connection()
    cursor = db.cursor()

    username = verify_token(st.session_state.token)

    if not username:
        st.error("🔒 Session expired")
        st.session_state.logged_in = False
        st.rerun()

    # ---------- SESSION INIT ----------
    if "transactions" not in st.session_state:
        st.session_state.transactions = pd.DataFrame(
            columns=["sales", "expenses"]
        )

    # ---------- SIDEBAR ----------
    st.sidebar.markdown("## 👤 Logged in as")
    st.sidebar.success(username)

    nav = st.sidebar.radio(
        "📌 Navigation",
        ["🏠 Dashboard", "➕ Add Transaction", "👤 Profile & Settings", "🚪 Logout"]
    )

    # ==========================================================
    # 🏠 DASHBOARD
    # ==========================================================
    if nav == "🏠 Dashboard":

        st.title("📊 Business Analytics Dashboard")

        df = st.session_state.transactions

        if not df.empty:

            total_sales = df["sales"].sum()
            total_expenses = df["expenses"].sum()
            profit = total_sales - total_expenses
            margin = (profit / total_sales) * 100 if total_sales > 0 else 0

            # KPI
            c1, c2, c3, c4 = st.columns(4)

            c1.metric("💰 Sales", f"{total_sales:.2f}")
            c2.metric("💸 Expenses", f"{total_expenses:.2f}")
            c3.metric("📈 Profit", f"{profit:.2f}")
            c4.metric("📊 Margin %", f"{margin:.2f}%")

            # STATUS
            if profit > 0:
                st.success("🟢 Business Running in PROFIT")
            elif profit < 0:
                st.error("🔴 Business Running in LOSS")
            else:
                st.warning("🟡 Break Even")

            # VISUALIZATION DATA
            chart_df = pd.DataFrame({
                "Category": ["Sales", "Expenses", "Profit"],
                "Amount": [total_sales, total_expenses, profit]
            })

            st.subheader("📊 Financial Overview")
            st.bar_chart(chart_df.set_index("Category"))

            st.subheader("📈 Transaction Trend")
            st.line_chart(df)

            # HISTORY TABLE
            st.subheader("📜 Transaction History")
            st.dataframe(df, use_container_width=True)

        else:
            st.info("No transactions yet — Add transactions to see analytics")

    # ==========================================================
    # ➕ ADD TRANSACTION
    # ==========================================================
    elif nav == "➕ Add Transaction":

        st.header("➕ Add Business Transactions")

        # -------- Manual Entry --------
        st.subheader("✍️ Manual Entry")

        sales = st.number_input("Enter Sales", min_value=0.0)
        expenses = st.number_input("Enter Expenses", min_value=0.0)

        if st.button("Add Transaction"):

            new_row = pd.DataFrame([{
                "sales": sales,
                "expenses": expenses
            }])

            st.session_state.transactions = pd.concat(
                [st.session_state.transactions, new_row],
                ignore_index=True
            )

            st.success("✅ Transaction Added")

        # -------- File Upload --------
        st.subheader("📂 Upload Transaction File")

        file = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx"]
        )

        if file:

            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

            df.columns = df.columns.str.strip().str.lower()

            if "sales" not in df.columns or "expenses" not in df.columns:
                st.error("File must contain sales and expenses columns")
            else:
                st.session_state.transactions = pd.concat(
                    [st.session_state.transactions, df[["sales", "expenses"]]],
                    ignore_index=True
                )

                st.success("✅ Transactions Imported Successfully")

    # ==========================================================
    # 👤 PROFILE
    # ==========================================================
    elif nav == "👤 Profile & Settings":

        st.header("👤 Profile Settings")

        cursor.execute(
            "SELECT username,email FROM users WHERE username=%s",
            (username,)
        )
        user_data = cursor.fetchone()

        if user_data:

            new_username = st.text_input("Username", value=user_data[0])
            new_email = st.text_input("Email", value=user_data[1])
            new_password = st.text_input("New Password", type="password")

            if st.button("Update Profile"):

                cursor.execute(
                    "UPDATE users SET username=%s,email=%s WHERE username=%s",
                    (new_username, new_email, username)
                )
                db.commit()

                if new_password:
                    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
                    cursor.execute(
                        "UPDATE users SET password=%s WHERE username=%s",
                        (hashed_pw, new_username)
                    )
                    db.commit()

                st.session_state.token = create_token(new_username)
                st.success("✅ Profile Updated")

    # ==========================================================
    # 🚪 LOGOUT
    # ==========================================================
    else:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.transactions = pd.DataFrame(columns=["sales", "expenses"])
        st.rerun()
