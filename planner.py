import random
import copy
from typing import List, Dict, Set, Tuple
import config
from recipe_client import Recipe, RecipeClient

# Days of the week
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

class MealPlanner:
    """Generates a weekly meal plan and scales ingredients to meet calorie targets."""
    
    def __init__(self, client: RecipeClient):
        self.client = client
        
    def generate_plan(self, history_titles: Set[str]) -> Dict[str, Dict[str, Recipe]]:
        """Generates a 7-day meal plan ensuring no repetitions with current week or history."""
        # Fetch candidate lists
        breakfasts_raw = self.client.fetch_recipes("breakfast")
        lunches_raw = self.client.fetch_recipes("lunch")
        dinners_raw = self.client.fetch_recipes("dinner")
        
        # Apply filters (cuisine and dairy-free check)
        from filters import filter_recipes
        breakfasts = filter_recipes(breakfasts_raw)
        lunches = filter_recipes(lunches_raw)
        dinners = filter_recipes(dinners_raw)
        
        # Ensure we have enough candidates
        if len(breakfasts) < 7 or len(lunches) < 7 or len(dinners) < 7:
            print("[Planner] Warning: Low recipe candidates. Some fallback or duplicate meals might occur.")
            
        # Shuffling candidates to introduce randomness each week
        random.shuffle(breakfasts)
        random.shuffle(lunches)
        random.shuffle(dinners)
        
        # Set of selected meals in this planning run to avoid duplicates within the same week
        selected_titles_this_week: Set[str] = set()
        
        # Combined history: items we must avoid (past 2 weeks + this week so far)
        forbidden_titles = set(history_titles)
        
        plan = {}
        
        for day in DAYS_OF_WEEK:
            plan[day] = {
                "breakfast": self._select_and_scale_recipe(
                    breakfasts, "breakfast", forbidden_titles, selected_titles_this_week
                ),
                "lunch": self._select_and_scale_recipe(
                    lunches, "lunch", forbidden_titles, selected_titles_this_week
                ),
                "dinner": self._select_and_scale_recipe(
                    dinners, "dinner", forbidden_titles, selected_titles_this_week
                )
            }
            
        return plan

    def _select_and_scale_recipe(
        self, 
        candidates: List[Recipe], 
        meal_type: str,
        forbidden_titles: Set[str],
        selected_titles_this_week: Set[str]
    ) -> Recipe:
        """Selects a recipe that isn't forbidden and scales its ingredients to the calorie target."""
        selected_recipe = None
        
        # 1. Search for a recipe that is not in the forbidden set
        for recipe in candidates:
            if recipe.title not in forbidden_titles and recipe.title not in selected_titles_this_week:
                selected_recipe = recipe
                break
                
        # 2. If all candidates are forbidden (e.g. database too small), relax the history constraint
        # but still avoid repeating in the same week
        if not selected_recipe:
            for recipe in candidates:
                if recipe.title not in selected_titles_this_week:
                    print(f"[Planner] History constraint relaxed for {meal_type}: selecting '{recipe.title}' (used in past 2 weeks)")
                    selected_recipe = recipe
                    break
                    
        # 3. Absolute fallback: pick any recipe if somehow everything is selected
        if not selected_recipe:
            if candidates:
                selected_recipe = candidates[0]
                print(f"[Planner] Absolute fallback for {meal_type}: repeating '{selected_recipe.title}' within the week")
            else:
                # Mock a quick recipe if candidates list is completely empty
                from recipe_client import Ingredient
                selected_recipe = Recipe(
                    id="fallback", title="Simple Salad", calories=250.0, servings=2, cuisine="Mediterranean", meal_type=meal_type,
                    ingredients=[Ingredient("mixed greens", 2.0, "cup"), Ingredient("olive oil", 1.0, "tbsp")]
                )
                
        # Add to the week's list to avoid duplication
        selected_titles_this_week.add(selected_recipe.title)
        
        # Make a deep copy to scale it without modifying the cached/source recipe
        scaled_recipe = copy.deepcopy(selected_recipe)
        
        # 4. Scale recipe calories and ingredients
        # Daily target is split: breakfast gets 22%, lunch and dinner get 39%
        allocation_fraction = config.MEAL_CALORIE_ALLOCATION[meal_type]
        target_calories = config.TOTAL_CALORIE_TARGET * allocation_fraction  # e.g., 4500 * 0.39 = 1755 kcal
        
        # Scale ingredients
        # Recipe ingredients amounts are normally for `recipe.servings` servings.
        # Total standard recipe calories = recipe.calories * recipe.servings.
        total_std_calories = scaled_recipe.calories * scaled_recipe.servings
        
        if total_std_calories > 0:
            scale_factor = target_calories / total_std_calories
        else:
            scale_factor = 1.0
            
        for ing in scaled_recipe.ingredients:
            ing.amount = round(ing.amount * scale_factor, 2)
            
        # Store scaled calories as total calories of this meal
        scaled_recipe.calories = target_calories
        # Mark servings as 2 (since it represents portions for Person A and Person B)
        scaled_recipe.servings = 2
        
        return scaled_recipe
