import streamlit as st
import pandas as pd
import psycopg2.extras
from db import get_connection

st.set_page_config(page_title="Ingredients", page_icon="🥦", layout="wide")
st.title("🥦 Ingredients")
st.markdown("Manage your master ingredients list. These will be available to attach to any recipe.")
st.divider()

# ── Search / Browse ────────────────────────────────────────
st.subheader("🔍 Browse Ingredients")
col1, col2 = st.columns(2)
search = col1.text_input("Search by name")
category_filter = col2.text_input("Filter by category (e.g. Dairy, Produce)")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = "SELECT id, name, category, created_at FROM ingredients WHERE 1=1"
    params = []

    if search.strip():
        query += " AND name ILIKE %s"
        params.append(f"%{search.strip()}%")
    if category_filter.strip():
        query += " AND category ILIKE %s"
        params.append(f"%{category_filter.strip()}%")

    query += " ORDER BY name ASC;"
    cur.execute(query, params)
    ingredients = cur.fetchall()
    cur.close()
    conn.close()

    if ingredients:
        df = pd.DataFrame(ingredients)
        df_display = df[["name", "category", "created_at"]].copy()
        df_display.columns = ["Ingredient", "Category", "Added On"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No ingredients found.")

except Exception as e:
    st.error(f"Could not load ingredients: {e}")

st.divider()

# ── Add Ingredient ─────────────────────────────────────────
st.subheader("➕ Add a New Ingredient")

with st.form("add_ingredient"):
    col1, col2 = st.columns(2)
    name = col1.text_input("Ingredient Name *")
    category = col2.text_input("Category (e.g. Dairy, Produce, Spice)")
    submitted = st.form_submit_button("Add Ingredient")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("**Ingredient name** is required.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO ingredients (name, category)
                    VALUES (%s, %s);
                """, (name.strip(), category.strip() or None))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ '{name.strip()}' added! Refresh to see it in the list.")
            except psycopg2.errors.UniqueViolation:
                st.error(f"'{name.strip()}' already exists in your ingredients list.")
            except Exception as e:
                st.error(f"Could not add ingredient: {e}")

st.divider()

# ── Edit / Delete ──────────────────────────────────────────
st.subheader("✏️ Edit or Delete an Ingredient")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM ingredients ORDER BY name;")
    all_ingredients = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load ingredients for editing: {e}")
    all_ingredients = []

if not all_ingredients:
    st.info("No ingredients available to edit or delete yet.")
else:
    ingredient_options = {r[1]: r[0] for r in all_ingredients}
    selected_name = st.selectbox("Select an ingredient to edit or delete", options=ingredient_options.keys())
    selected_id = ingredient_options[selected_name]

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM ingredients WHERE id = %s;", (selected_id,))
        ingredient = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Could not load ingredient details: {e}")
        ingredient = None

    if ingredient:
        with st.form("edit_ingredient"):
            st.markdown(f"**Editing:** {ingredient['name']}")
            col1, col2 = st.columns(2)
            edit_name = col1.text_input("Ingredient Name *", value=ingredient["name"])
            edit_category = col2.text_input("Category", value=ingredient["category"] or "")
            update_btn = st.form_submit_button("💾 Save Changes")

            if update_btn:
                errors = []
                if not edit_name.strip():
                    errors.append("**Ingredient name** is required.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE ingredients
                            SET name = %s, category = %s
                            WHERE id = %s;
                        """, (edit_name.strip(), edit_category.strip() or None, selected_id))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Ingredient updated! Refresh to see changes.")
                    except psycopg2.errors.UniqueViolation:
                        st.error(f"'{edit_name.strip()}' already exists in your ingredients list.")
                    except Exception as e:
                        st.error(f"Could not update ingredient: {e}")

        st.markdown("---")
        st.markdown("**Danger Zone**")
        if st.checkbox(f"I want to delete **{ingredient['name']}**"):
            if st.button("🗑️ Confirm Delete", type="primary"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM ingredients WHERE id = %s;", (selected_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("🗑️ Ingredient deleted. Refresh to update the list.")
                except Exception as e:
                    st.error(f"Could not delete ingredient: {e}")