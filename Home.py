import streamlit as st
import pandas as pd
from db import get_connection

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="🍽️ Recipe & Meal Planner",
    page_icon="🍽️",
    layout="wide"
)

# ── Header ─────────────────────────────────────────────────
st.title("🍽️ Recipe & Meal Planner")
st.markdown("Your personal kitchen command center — save recipes, plan your week, and stay organized.")
st.divider()

# ── Summary Metrics ────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM recipes;")
    total_recipes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ingredients;")
    total_ingredients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM meal_plans;")
    total_plans = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM meal_plan_recipes;")
    total_meals_planned = cur.fetchone()[0]

    cur.close()
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📖 Recipes", total_recipes)
    col2.metric("🥦 Ingredients", total_ingredients)
    col3.metric("📅 Meal Plans", total_plans)
    col4.metric("🍴 Meals Planned", total_meals_planned)

except Exception as e:
    st.error(f"Could not load dashboard data: {e}")

st.divider()

# ── Recent Recipes ─────────────────────────────────────────
st.subheader("🕐 Recently Added Recipes")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cur.execute("""
        SELECT title, cuisine, prep_time_min, cook_time_min, servings, created_at
        FROM recipes
        ORDER BY created_at DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["Title", "Cuisine", "Prep (min)", "Cook (min)", "Servings", "Added On"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No recipes yet — head to the Recipes page to add your first one!")

except Exception as e:
    st.error(f"Could not load recent recipes: {e}")

st.divider()

# ── Upcoming Meal Plans ────────────────────────────────────
st.subheader("📅 Active Meal Plans")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cur.execute("""
        SELECT name, start_date, end_date, notes
        FROM meal_plans
        ORDER BY start_date DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["Plan Name", "Start Date", "End Date", "Notes"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No meal plans yet — create one in the Meal Plans page!")

except Exception as e:
    st.error(f"Could not load meal plans: {e}")