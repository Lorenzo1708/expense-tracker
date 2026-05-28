import os
from datetime import datetime, timedelta, timezone

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

from base_models import Balance, Expense, Profile

st.set_page_config(page_title="Expense Tracker", page_icon=":material/account_balance_wallet:")


@st.cache_resource
def _load_client() -> Client:
    load_dotenv()

    if not ((supabase_url := os.getenv("SUPABASE_URL")) and (supabase_key := os.getenv("SUPABASE_KEY"))):
        raise ValueError("Missing one or more of these environment variables:\n- SUPABASE_URL\n- SUPABASE_KEY")

    return create_client(supabase_url, supabase_key)


try:
    _CLIENT = _load_client()
except Exception as exception:
    st.error(f"Error in _load_client():\n{exception}")

    st.stop()


@st.cache_resource
def _load_user_id() -> str:
    return Profile.model_validate(_CLIENT.table("profiles").select("*").eq("name", "Lorenzo").single().execute().data).user_id


try:
    _USER_ID = _load_user_id()
except Exception as exception:
    st.error(f"Error in _load_user_id():\n{exception}")

    st.stop()


if "amount" not in st.session_state:
    st.session_state["amount"] = Balance.model_validate(_CLIENT.table("balances").select("*").eq("user_id", _USER_ID).single().execute().data).amount

_AMOUNT = st.session_state["amount"]

if "expenses" not in st.session_state:
    datetime_now = datetime.now()
    days = datetime_now.weekday()
    st.session_state["expenses"] = [Expense.model_validate(data) for data in _CLIENT.table("expenses").select("*").eq("user_id", _USER_ID).gte("date", (datetime_now - timedelta(days)).date()).lte("date", (datetime_now + timedelta(6.0 - days)).date()).order("date", desc=True).order("created_at").execute().data]

_EXPENSES: list[Expense] = st.session_state["expenses"]


@st.dialog("Add expense")
def _add_expense() -> None:
    with st.form("create-expense"):
        name = st.text_input(":material/badge: Name", placeholder="Enter the name...")
        cost = st.number_input(":material/add_card: Cost")
        date = st.date_input(":material/date_range: Date", datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3.0))), format="DD/MM/YYYY")

        with st.container(horizontal_alignment="right"):
            if st.form_submit_button(":material/add:"):
                try:
                    with st.spinner("Please wait...", show_time=True):
                        _CLIENT.table("expenses").insert({"user_id": _USER_ID, "name": name, "cost": cost, "date": date.strftime("%Y-%m-%d")}).execute()

                        st.session_state["amount"] = Balance.model_validate(_CLIENT.table("balances").select("*").eq("user_id", _USER_ID).single().execute().data).amount
                        datetime_now = datetime.now()
                        days = datetime_now.weekday()
                        st.session_state["expenses"] = [Expense.model_validate(data) for data in _CLIENT.table("expenses").select("*").eq("user_id", _USER_ID).gte("date", (datetime_now - timedelta(days)).date()).lte("date", (datetime_now + timedelta(6.0 - days)).date()).order("date", desc=True).order("created_at").execute().data]

                    st.rerun()
                except Exception as exception:
                    st.error(f"Error in _add_expense():\n{exception}")


@st.dialog("Edit expense")
def _edit_expense(index: int) -> None:
    with st.form("edit-expense"):
        expense = _EXPENSES[index]
        name = st.text_input(":material/badge: Name", expense.name)
        cost = st.number_input(":material/add_card: Cost", value=expense.cost)
        date = st.date_input(":material/date_range: Date", expense.date, format="DD/MM/YYYY")

        with st.container(horizontal_alignment="right"):
            if st.form_submit_button(":material/edit:"):
                try:
                    with st.spinner("Please wait...", show_time=True):
                        _CLIENT.table("expenses").update({"name": name, "cost": cost, "date": date.strftime("%Y-%m-%d")}).eq("id", expense.id).execute()

                        st.session_state["amount"] = Balance.model_validate(_CLIENT.table("balances").select("*").eq("user_id", _USER_ID).single().execute().data).amount
                        datetime_now = datetime.now()
                        days = datetime_now.weekday()
                        st.session_state["expenses"] = [Expense.model_validate(data) for data in _CLIENT.table("expenses").select("*").eq("user_id", _USER_ID).gte("date", (datetime_now - timedelta(days)).date()).lte("date", (datetime_now + timedelta(6.0 - days)).date()).order("date", desc=True).order("created_at").execute().data]

                    st.rerun()
                except Exception as exception:
                    st.error(f"Error in _edit_expense():\n{exception}")


@st.dialog("Delete expense")
def _delete_expense(index: int) -> None:
    with st.container(border=True, horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        expense = _EXPENSES[index]

        with st.container():
            st.write(f":material/badge: {expense.name}")
            st.badge(f"{expense.cost:.2f}", icon=":material/add_card:", color="green")
            st.badge(datetime.strptime(expense.date, "%Y-%m-%d").strftime("%a, %d/%m/%y"), icon=":material/date_range:")

        with st.container(horizontal_alignment="right"):
            if st.button(":material/delete:", type="primary"):
                try:
                    with st.spinner("Please wait...", show_time=True):
                        _CLIENT.table("expenses").delete().eq("id", expense.id).execute()

                        st.session_state["amount"] = Balance.model_validate(_CLIENT.table("balances").select("*").eq("user_id", _USER_ID).single().execute().data).amount
                        datetime_now = datetime.now()
                        days = datetime_now.weekday()
                        st.session_state["expenses"] = [Expense.model_validate(data) for data in _CLIENT.table("expenses").select("*").eq("user_id", _USER_ID).gte("date", (datetime_now - timedelta(days)).date()).lte("date", (datetime_now + timedelta(6.0 - days)).date()).order("date", desc=True).order("created_at").execute().data]

                    st.rerun()
                except Exception as exception:
                    st.error(f"Error in _delete_expense():\n{exception}")


st.subheader(f":material/balance: Balance: :{"red" if _AMOUNT < 0.0 else "green"}[R$ {_AMOUNT:.2f}]", anchor=False, text_alignment="center")
st.space()

with st.container(horizontal_alignment="center"):
    if st.button(":material/add:"):
        _add_expense()

st.space()

for count, expense in enumerate(_EXPENSES):
    with st.container(border=True, horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        with st.container():
            st.write(f":material/badge: {expense.name}")
            st.badge(f"R$ {expense.cost:.2f}", icon=":material/add_card:", color="green")
            st.badge(datetime.strptime(expense.date, "%Y-%m-%d").strftime("%a, %d/%m/%y"), icon=":material/date_range:")

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button(":material/edit:", f":material/edit:_{count}"):
                _edit_expense(count)

            if st.button(":material/delete:", f":material/delete:_{count}", type="primary"):
                _delete_expense(count)

with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="top"):
    if st.button(":material/keyboard_arrow_down:"):
        pass  # TODO

    if st.button(":material/keyboard_arrow_up:"):
        pass  # TODO
