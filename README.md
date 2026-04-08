# streamlit-recipe-app
Recipe and Meal tracker app built using streamlit and PostgreSQL

Link to streamlit app: https://homepy-jt5bgzigaqreq2e56zk3pv.streamlit.app/

How to run locally: Download files and arrange in proper file structure and open on VSCode. Open new terminal and type "streamlit run Home.py" and press enter. Click the link the shows in the output 

<img width="721" height="770" alt="ERD-meals" src="https://github.com/user-attachments/assets/77f593ab-3df2-4511-88ad-45cf829cd4e0" />

* Table Descriptions:
  * recipes — Stores each recipe's title, description, instructions, prep/cook times, servings, and cuisine type.
  * ingredients — Master list of ingredients with an optional category (e.g. Dairy, Produce, Spice) that can be reused across recipes.
  * recipe_ingredients — Junction table linking recipes to ingredients (many-to-many). Stores the quantity and unit for each ingredient per recipe.
  * meal_plans — Named meal plans with a start/end date and optional notes (e.g. "Week of April 7").
  * meal_plan_recipes — Junction table linking meal plans to recipes (many-to-many). Stores the day of the week and meal type (Breakfast, Lunch, Dinner, Snack) for each assignment.
