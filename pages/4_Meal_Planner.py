import streamlit as st
import pandas as pd
import psycopg2.extras
from db import get_connection

st.set_page_config(page_title="Meal Planner", page_icon="🍴", layout="wide")
st.title("🍴 Meal Planner")
st.markdown("Assign recipes to days and meal types within a meal plan.")
st.divider()

# ── Select a Meal Plan ─────────────────────────────────────
st.subheader("📅 Select a Meal Plan")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM meal_plans ORDER BY start_date DESC;")
    all_plans = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load meal plans: {e}")
    all_plans = []

if not all_plans:
    st.warning("No meal plans found. Create one in the Meal Plans page first!")
    st.stop()

plan_options = {r[1]: r[0] for r in all_plans}
selected_plan_name = st.selectbox("Choose a meal plan", options=plan_options.keys())
selected_plan_id = plan_options[selected_plan_name]

st.divider()

# ── Current Assignments for this Plan ─────────────────────
st.subheader(f"🗓️ Current Schedule — {selected_plan_name}")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT mpr.id, r.title AS recipe, mpr.day_of_week, mpr.meal_type
        FROM meal_plan_recipes mpr
        JOIN recipes r ON r.id = mpr.recipe_id
        WHERE mpr.meal_plan_id = %s
        ORDER BY
            CASE mpr.day_of_week
                WHEN 'Monday'    THEN 1
                WHEN 'Tuesday'   THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday'  THEN 4
                WHEN 'Friday'    THEN 5
                WHEN 'Saturday'  THEN 6
                WHEN 'Sunday'    THEN 7
            END,
            CASE mpr.meal_type
                WHEN 'Breakfast' THEN 1
                WHEN 'Lunch'     THEN 2
                WHEN 'Dinner'    THEN 3
                WHEN 'Snack'     THEN 4
            END;
    """, (selected_plan_id,))
    assignments = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load assignments: {e}")
    assignments = []

if assignments:
    df = pd.DataFrame(assignments)
    df_display = df[["day_of_week", "meal_type", "recipe"]].copy()
    df_display.columns = ["Day", "Meal Type", "Recipe"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ── Remove an Assignment ───────────────────────────────
    st.markdown("**Remove an Assignment**")
    remove_options = {
        f"{a['day_of_week']} — {a['meal_type']} — {a['recipe']}": a["id"]
        for a in assignments
    }
    selected_remove = st.selectbox("Select an assignment to remove", options=remove_options.keys())
    remove_id = remove_options[selected_remove]

    if st.checkbox(f"I want to remove **{selected_remove}**"):
        if st.button("🗑️ Confirm Remove", type="primary"):
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM meal_plan_recipes WHERE id = %s;", (remove_id,))
                conn.commit()
                cur.close()
                conn.close()
                st.success("✅ Assignment removed. Refresh to update the schedule.")
            except Exception as e:
                st.error(f"Could not remove assignment: {e}")
else:
    st.info("No recipes assigned to this plan yet. Add some below!")

st.divider()

# ── Assign a Recipe ────────────────────────────────────────
st.subheader("➕ Assign a Recipe to this Plan")

# Dynamic dropdowns — both pulled from DB
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM meal_plans ORDER BY start_date DESC;")
    cur.execute("SELECT id, title FROM recipes ORDER BY title;")
    all_recipes = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load recipes: {e}")
    all_recipes = []

if not all_recipes:
    st.warning("No recipes found. Add some in the Recipes page first!")
else:
    # Day and meal type options stored in DB via lookup — using static lists
    # that map to what's already constrained in the schema
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"]

    recipe_options = {r[1]: r[0] for r in all_recipes}

    with st.form("assign_recipe"):
        col1, col2, col3 = st.columns(3)
        selected_recipe_name = col1.selectbox("Recipe *", options=recipe_options.keys())
        selected_day = col2.selectbox("Day of Week *", options=DAYS)
        selected_meal_type = col3.selectbox("Meal Type *", options=MEAL_TYPES)
        submitted = st.form_submit_button("Assign Recipe")

        if submitted:
            selected_recipe_id = recipe_options[selected_recipe_name]
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO meal_plan_recipes (meal_plan_id, recipe_id, day_of_week, meal_type)
                    VALUES (%s, %s, %s, %s);
                """, (selected_plan_id, selected_recipe_id, selected_day, selected_meal_type))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ {selected_recipe_name} added to {selected_day} {selected_meal_type}! Refresh to see the update.")
            except psycopg2.errors.UniqueViolation:
                st.error(f"'{selected_recipe_name}' is already assigned to {selected_day} {selected_meal_type} in this plan.")
            except Exception as e:
                st.error(f"Could not assign recipe: {e}")