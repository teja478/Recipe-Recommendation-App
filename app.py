import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import re
import random
import json
import os

# ---------------- USER STORAGE ----------------
USER_FILE = "users.json"

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ---------------- USER SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---------------- PASSWORD VALIDATION ----------------
def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters,1 uppercase, 1 lowercase, and 1 number"
    if not re.search(r"[A-Z]", password):
        return False, "Password must be at least 8 characters,1 uppercase, 1 lowercase, and 1 number"
    if not re.search(r"[a-z]", password):
        return False, "Password must be at least 8 characters,1 uppercase, 1 lowercase, and 1 number"
    if not re.search(r"[0-9]", password):
        return False, "Password must be at least 8 characters,1 uppercase, 1 lowercase, and 1 number"
    return True, ""

# ---------------- AUTH UI ----------------
def auth_page():

    # ✅ UI ADDITION ONLY
    st.markdown("""
    <div style='background: linear-gradient(135deg, #cce7ff, #99ccff);
                padding: 30px;
                border-radius: 15px;
                text-align:center;'>
        <h1 style='color:#003366;'>🍽 Smart Recipe Finder</h1>
    </div>
    """, unsafe_allow_html=True)

    st.title("🔐 Login / Signup")

    menu = st.radio("Select Option", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if menu == "Login":
        if st.button("Login"):
            users = load_users()

            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.success(f"✅ Welcome {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    else:
        if st.button("Signup"):
            users = load_users()

            if username in users:
                st.error("❌ Username already exists")
            elif username == "" or password == "":
                st.warning("⚠️ Please enter username & password")
            else:
                valid, message = is_valid_password(password)

                if not valid:
                    st.error(f"❌ {message}")
                else:
                    users[username] = password
                    save_users(users)
                    st.success("✅ Signup successful! Now login.")

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Recipe Finder", layout="wide")

# ---------------- FILES ----------------
FAV_FILE = "favorites.json"
RATINGS_FILE = "ratings.json"

# ---------------- ROUTING ----------------
if not st.session_state.logged_in:
    auth_page()

    # ✅ FOOTER (LOGIN PAGE)
    st.markdown("""
    <div style='position:fixed; bottom:0; width:100%;
                text-align:center; background:rgba(0,0,0,0.7);
                color:white; padding:10px;'>
        🍽 Smart Recipe Finder | Built with ❤️ using Streamlit
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ---------------- USER INFO ----------------
col1, col2 = st.columns([8,1])

with col1:
    st.markdown(f"👤 Logged in as: **{st.session_state.current_user}**")

with col2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

# ---------------- FAVORITES (UPDATED) ----------------
def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):  # old format fix
                    return {}
                return data
        except:
            return {}
    return {}

def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f)

# ---------------- RATINGS ----------------
def load_ratings():
    if os.path.exists(RATINGS_FILE):
        try:
            with open(RATINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_ratings(ratings):
    with open(RATINGS_FILE, "w") as f:
        json.dump(ratings, f)

def get_average_rating(name):
    if name in st.session_state.ratings:
        ratings_list = st.session_state.ratings[name]
        if ratings_list:
            avg = sum(ratings_list)/len(ratings_list)
            return round(avg, 1)
    return None

def add_rating(name, value):
    if name not in st.session_state.ratings:
        st.session_state.ratings[name] = []
    st.session_state.ratings[name].append(value)
    save_ratings(st.session_state.ratings)

# ---------------- SESSION ----------------
if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()

if "ratings" not in st.session_state:
    st.session_state.ratings = load_ratings()

if "results" not in st.session_state:
    st.session_state.results = None

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "dummy" not in st.session_state:
    st.session_state.dummy = 0

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #667eea, #764ba2); }
.title { text-align:center; font-size:50px; color:white; }
.card {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(15px);
    padding:20px;
    border-radius:20px;
    margin-bottom:20px;
    color:white;
}
.tag {
    display:inline-block;
    background: rgba(255,255,255,0.3);
    padding:6px 12px;
    margin:4px;
    border-radius:15px;
}
.score {
    float:right;
    background:#ff4b4b;
    padding:5px 10px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center; font-size:50px; color:white;'>
🍽 Smart Recipe Finder
</h1>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("recipes.csv")
    df.columns = df.columns.str.lower()

# ✅ Convert 'title' column → 'name'
    if "title" in df.columns:
        df.rename(columns={"title": "name"}, inplace=True)

# fallback (only if neither exists)
    if "name" not in df.columns:
        df["name"] = "Recipe"
    if "instructions" not in df.columns:
        df["instructions"] = ""
    return df

df = load_data()

# ---------------- HELPERS ----------------
def clean_ingredients(text):
    try:
        items = ast.literal_eval(text)
    except:
        items = str(text).split(",")
    return [re.sub(r'\d+|[^\w\s]', '', i.lower()).strip() for i in items if i]

def clean_user_input(user_input):
    return [re.sub(r'\d+|[^\w\s]', '', i.lower()).strip() for i in user_input.split(",") if i.strip()]

def tags(items):
    return " ".join([f"<span class='tag'>{i}</span>" for i in items])

def steps(text):
    parts = re.split(r'\.\s+|\n', text)
    return "<br>".join([f"➡️ {p.strip()}" for p in parts if p.strip()])

# ---------------- FAVORITES DISPLAY ----------------
st.subheader("❤️ Your Saved Recipes")

user = st.session_state.current_user
user_favs = st.session_state.favorites.get(user, [])

if user_favs:
    for i, fav in enumerate(user_favs):
        ing_list = clean_ingredients(fav.get("ingredients", ""))

        avg = get_average_rating(fav.get("name"))
        rating_html = f"<br><b>⭐ Rating:</b> {'★'*int(avg)}{'☆'*(5-int(avg))} ({avg}/5)" if avg else ""

        st.markdown(f"""
        <div class='card'>
        <b>{fav.get('name')}</b>{rating_html}
        <hr>
        <b>🟢 Ingredients:</b><br>{tags(ing_list)}
        <br><br>
        <b>⏱ Time:</b> TBD
        <br><br>
        <b>👨‍🍳 Steps:</b><br>{steps(fav.get('instructions'))}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"❌ Remove {fav.get('name')}", key=f"remove_{i}"):
            st.session_state.favorites[user].pop(i)
            save_favorites(st.session_state.favorites)
            st.rerun()
else:
    st.info("No saved recipes yet")

st.markdown("---")

# ---------------- COOKING TIME ----------------
def estimate_time(instructions):
    if not instructions or instructions.strip() == "":
        return "⏱ ~15 mins"

    text = instructions.lower()
    steps_list = re.split(r'\.\s+|\n', text)
    steps_count = len([s for s in steps_list if s.strip()])

    time = 8 + steps_count * 2

    keywords = {
        "chop": 3, "cut": 3,
        "fry": 5, "saute": 5,
        "boil": 7,
        "simmer": 10,
        "bake": 20,
        "roast": 18,
        "grill": 15,
        "pressure": 12,
        "marinate": 15,
        "slow": 30
    }

    for word, t in keywords.items():
        if word in text:
            time += t

    if time < 10:
        time = 10
    if time > 60:
        time = 60 + (time - 60)//2

    return f"⏱ {time} mins"

# ---------------- SAVE FAVORITES ----------------
def save_recipe(recipe_data):
    user = st.session_state.current_user

    if user not in st.session_state.favorites:
        st.session_state.favorites[user] = []

    if recipe_data not in st.session_state.favorites[user]:
        st.session_state.favorites[user].append(recipe_data)
        save_favorites(st.session_state.favorites)
        st.toast("Saved ❤️")

# ---------------- AUTOCOMPLETE ----------------
@st.cache_data
def get_all_ingredients(df):
    s = set()
    for row in df["ingredients"]:
        s.update(clean_ingredients(row))
    return sorted(s)

all_ingredients = get_all_ingredients(df)

# ---------------- SIMILARITY ----------------
@st.cache_resource
def build_model(data):
    corpus = data["ingredients"].astype(str).tolist()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf_matrix

vectorizer, tfidf_matrix = build_model(df)

def get_similar(df, user_input):
    user_vec = vectorizer.transform([user_input])
    sim = cosine_similarity(user_vec, tfidf_matrix)
    df["score"] = sim.flatten()
    return df.sort_values("score", ascending=False).head(5)

# ---------------- INPUT ----------------
selected = st.multiselect("Select ingredients", all_ingredients)
manual = st.text_input("Or type manually")
user_input = manual + "," + ",".join(selected)

if st.button("Find Recipes"):
    if not user_input.strip():
        st.warning("⚠️ Please enter ingredients")
    else:
        st.session_state.user_input = user_input
        st.session_state.results = get_similar(df.copy(), user_input)

# ---------------- RESULTS ----------------
if st.session_state.results is not None:
    results = st.session_state.results
    user_clean = clean_user_input(st.session_state.user_input)

    st.subheader("✨ Recommended Recipes")

    for i, (_, row) in enumerate(results.iterrows()):
        ing_list = clean_ingredients(row["ingredients"])
        available = [i for i in ing_list if any(u in i for u in user_clean)]
        missing = [i for i in ing_list if not any(u in i for u in user_clean)]

        if not available:
            available = ["None"]
        if not missing:
            missing = ["Nothing — you have everything! 🎉"]

        avg = get_average_rating(row["name"])
        rating_html = f"<br><b>⭐ Rating:</b> {'★'*int(avg)}{'☆'*(5-int(avg))} ({avg}/5)" if avg else ""

        st.markdown(f"""
        <div class='card'>
        <b>{row['name']}</b>{rating_html}
        <span class='score'>{round(row['score']*100,1)}%</span>
        <hr>
        <b>⏱ Cooking Time:</b> {estimate_time(row['instructions'])}
        <br><br>
        <b>🟢 You Have:</b><br>{tags(available)}
        <br><br>
        <b>🔴 Missing:</b><br>{tags(missing)}
        <br><br>
        <b>👨‍🍳 Steps:</b><br>{steps(row['instructions'])}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"❤️ Save {row['name']}", key=f"save_{i}"):
            recipe_data = {
                "name": row["name"],
                "ingredients": row["ingredients"],
                "instructions": row["instructions"]
            }
            save_recipe(recipe_data)

# ✅ FOOTER (MAIN APP)
st.markdown("""
<div style='position:fixed; bottom:0; width:100%;
            text-align:center; background:rgba(0,0,0,0.7);
            color:white; padding:10px;'>
    🍽 Smart Recipe Finder | Built with ❤️ using Streamlit
</div>
""", unsafe_allow_html=True)