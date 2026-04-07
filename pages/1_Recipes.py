import streamlit as st
import pandas as pd
import psycopg2.extras
from db import get_connection

st.set_page_config(page_title="Recipes", page_icon="📖", layout="wide")
st.title("📖 Recipes")
st.markdown("Add, browse, edit, and delete your recipes.")
st.divider()

# ── Search / Filter ────────────────────────────────────────
st.subheader("🔍 Browse Recipes")
col1, col2 = st.columns(2)
search = col1.text_input("Search by title")
cuisine_filter = col2.text_input("Filter by cuisine")

try:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT id, title, cuisine, prep_time_min, cook_time_min, servings, created_at
        FROM recipes
        WHERE 1=1
    """
    params = []

    if search.strip():
        query += " AND title ILIKE %s"
        params.append(f"%{search.strip()}%")
    if cuisine_filter.strip():
        query += " AND cuisine ILIKE %s"
        params.append(f"%{cuisine_filter.strip()}%")

    query += " ORDER BY created_at DESC;"
    cur.execute(query, params)
    recipes = cur.fetchall()
    cur.close()
    conn.close()

    if recipes:
        df = pd.DataFrame(recipes)
        df_display = df[["title", "cuisine", "prep_time_min", "cook_time_min", "servings", "created_at"]].copy()
        df_display.columns = ["Title", "Cuisine", "Prep (min)", "Cook (min)", "Servings", "Added On"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No recipes found.")

except Exception as e:
    st.error(f"Could not load recipes: {e}")

st.divider()

# ── Add Recipe ─────────────────────────────────────────────
st.subheader("➕ Add a New Recipe")

with st.form("add_recipe"):
    title = st.text_input("Recipe Title *")
    description = st.text_area("Description")
    instructions = st.text_area("Instructions")
    col1, col2, col3, col4 = st.columns(4)
    prep_time = col1.number_input("Prep Time (min)", min_value=0, step=1)
    cook_time = col2.number_input("Cook Time (min)", min_value=0, step=1)
    servings = col3.number_input("Servings", min_value=1, step=1)
    cuisine = col4.text_input("Cuisine (e.g. Italian)")
    submitted = st.form_submit_button("Add Recipe")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("**Title** is required.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO recipes (title, description, instructions, prep_time_min, cook_time_min, servings, cuisine)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (title.strip(), description.strip(), instructions.strip(), prep_time, cook_time, servings, cuisine.strip()))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ '{title.strip()}' added successfully! Refresh to see it in the list.")
            except Exception as e:
                st.error(f"Could not add recipe: {e}")

st.divider()

# ── Edit / Delete ──────────────────────────────────────────
st.subheader("✏️ Edit or Delete a Recipe")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM recipes ORDER BY title;")
    all_recipes = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load recipes for editing: {e}")
    all_recipes = []

if not all_recipes:
    st.info("No recipes available to edit or delete yet.")
else:
    recipe_options = {f"{r[1]}": r[0] for r in all_recipes}
    selected_name = st.selectbox("Select a recipe to edit or delete", options=recipe_options.keys())
    selected_id = recipe_options[selected_name]

    # Load selected recipe data
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM recipes WHERE id = %s;", (selected_id,))
        recipe = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Could not load recipe details: {e}")
        recipe = None

    if recipe:
        with st.form("edit_recipe"):
            st.markdown(f"**Editing:** {recipe['title']}")
            edit_title = st.text_input("Recipe Title *", value=recipe["title"])
            edit_description = st.text_area("Description", value=recipe["description"] or "")
            edit_instructions = st.text_area("Instructions", value=recipe["instructions"] or "")
            col1, col2, col3, col4 = st.columns(4)
            edit_prep = col1.number_input("Prep Time (min)", min_value=0, step=1, value=recipe["prep_time_min"] or 0)
            edit_cook = col2.number_input("Cook Time (min)", min_value=0, step=1, value=recipe["cook_time_min"] or 0)
            edit_servings = col3.number_input("Servings", min_value=1, step=1, value=recipe["servings"] or 1)
            edit_cuisine = col4.text_input("Cuisine", value=recipe["cuisine"] or "")
            update_btn = st.form_submit_button("💾 Save Changes")

            if update_btn:
                errors = []
                if not edit_title.strip():
                    errors.append("**Title** is required.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE recipes
                            SET title = %s, description = %s, instructions = %s,
                                prep_time_min = %s, cook_time_min = %s,
                                servings = %s, cuisine = %s
                            WHERE id = %s;
                        """, (edit_title.strip(), edit_description.strip(), edit_instructions.strip(),
                              edit_prep, edit_cook, edit_servings, edit_cuisine.strip(), selected_id))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Recipe updated! Refresh to see changes.")
                    except Exception as e:
                        st.error(f"Could not update recipe: {e}")

        # Delete outside the form
        st.markdown("---")
        st.markdown("**Danger Zone**")
        if st.checkbox(f"I want to delete **{recipe['title']}**"):
            if st.button("🗑️ Confirm Delete", type="primary"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM recipes WHERE id = %s;", (selected_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("🗑️ Recipe deleted. Refresh the page to update the list.")
                except Exception as e:
                    st.error(f"Could not delete recipe: {e}")