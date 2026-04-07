import streamlit as st
import pandas as pd
import psycopg2.extras
from db import get_connection

st.set_page_config(page_title="Meal Plans", page_icon="📅", layout="wide")
st.title("📅 Meal Plans")
st.markdown("Create and manage your weekly meal plans.")
st.divider()

# ── Browse Meal Plans ──────────────────────────────────────
st.subheader("🔍 Your Meal Plans")
search = st.text_input("Search by plan name")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = "SELECT id, name, start_date, end_date, notes, created_at FROM meal_plans WHERE 1=1"
    params = []

    if search.strip():
        query += " AND name ILIKE %s"
        params.append(f"%{search.strip()}%")

    query += " ORDER BY start_date DESC;"
    cur.execute(query, params)
    plans = cur.fetchall()
    cur.close()
    conn.close()

    if plans:
        df = pd.DataFrame(plans)
        df_display = df[["name", "start_date", "end_date", "notes", "created_at"]].copy()
        df_display.columns = ["Plan Name", "Start Date", "End Date", "Notes", "Created On"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No meal plans found.")

except Exception as e:
    st.error(f"Could not load meal plans: {e}")

st.divider()

# ── Add Meal Plan ──────────────────────────────────────────
st.subheader("➕ Create a New Meal Plan")

with st.form("add_meal_plan"):
    name = st.text_input("Plan Name * (e.g. 'Week of April 7')")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date *")
    end_date = col2.date_input("End Date *")
    notes = st.text_area("Notes (optional)")
    submitted = st.form_submit_button("Create Meal Plan")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("**Plan name** is required.")
        if end_date < start_date:
            errors.append("**End date** must be on or after the start date.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO meal_plans (name, start_date, end_date, notes)
                    VALUES (%s, %s, %s, %s);
                """, (name.strip(), start_date, end_date, notes.strip() or None))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ '{name.strip()}' created! Refresh to see it in the list.")
            except Exception as e:
                st.error(f"Could not create meal plan: {e}")

st.divider()

# ── Edit / Delete ──────────────────────────────────────────
st.subheader("✏️ Edit or Delete a Meal Plan")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM meal_plans ORDER BY start_date DESC;")
    all_plans = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load meal plans for editing: {e}")
    all_plans = []

if not all_plans:
    st.info("No meal plans available to edit or delete yet.")
else:
    plan_options = {r[1]: r[0] for r in all_plans}
    selected_name = st.selectbox("Select a meal plan to edit or delete", options=plan_options.keys())
    selected_id = plan_options[selected_name]

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM meal_plans WHERE id = %s;", (selected_id,))
        plan = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Could not load meal plan details: {e}")
        plan = None

    if plan:
        with st.form("edit_meal_plan"):
            st.markdown(f"**Editing:** {plan['name']}")
            edit_name = st.text_input("Plan Name *", value=plan["name"])
            col1, col2 = st.columns(2)
            edit_start = col1.date_input("Start Date *", value=plan["start_date"])
            edit_end = col2.date_input("End Date *", value=plan["end_date"])
            edit_notes = st.text_area("Notes", value=plan["notes"] or "")
            update_btn = st.form_submit_button("💾 Save Changes")

            if update_btn:
                errors = []
                if not edit_name.strip():
                    errors.append("**Plan name** is required.")
                if edit_end < edit_start:
                    errors.append("**End date** must be on or after the start date.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE meal_plans
                            SET name = %s, start_date = %s, end_date = %s, notes = %s
                            WHERE id = %s;
                        """, (edit_name.strip(), edit_start, edit_end,
                              edit_notes.strip() or None, selected_id))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Meal plan updated! Refresh to see changes.")
                    except Exception as e:
                        st.error(f"Could not update meal plan: {e}")

        st.markdown("---")
        st.markdown("**Danger Zone**")
        if st.checkbox(f"I want to delete **{plan['name']}**"):
            if st.button("🗑️ Confirm Delete", type="primary"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM meal_plans WHERE id = %s;", (selected_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("🗑️ Meal plan deleted. Refresh to update the list.")
                except Exception as e:
                    st.error(f"Could not delete meal plan: {e}")