import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import requests
import config

@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str
    category: str = "others"  # vegetables, proteins, pantry staples, dairy alternatives, others

@dataclass
class Recipe:
    id: str
    title: str
    calories: float          # Calories per serving
    servings: int            # Standard servings count
    cuisine: str
    meal_type: str          # breakfast, lunch, dinner
    ingredients: List[Ingredient] = field(default_factory=list)
    source_url: str = ""

class RecipeClient:
    """Client for fetching recipes. Falls back to a local Mock client if API key is missing."""
    
    def __init__(self):
        self.api_key = config.RECIPE_API_KEY
        self.is_mock = config.IS_MOCK_MODE
        
    def fetch_recipes(self, meal_type: str) -> List[Recipe]:
        """Fetches recipes for a given meal type (breakfast, lunch, dinner)."""
        if self.is_mock:
            print(f"[Client] Running in MOCK MODE. Retrieving local mock recipes for: {meal_type}")
            return self._get_mock_recipes(meal_type)
            
        print(f"[Client] Fetching live recipes from Spoonacular API for: {meal_type}")
        try:
            # Map meal_type to Spoonacular query parameters
            # Spoonacular types: breakfast, main course, salad, soup, etc.
            spoonacular_type = "breakfast" if meal_type == "breakfast" else "main course"
            
            # Request parameters:
            # - diet: dairyFree (respects lactose intolerance)
            # - cuisine: Mediterranean,Italian,Greek,Spanish,French (Mediterranean-focused and Western/European)
            # - addRecipeInformation: True (gets ingredients list and source URL)
            # - addRecipeNutrition: True (gets nutritional info / calories)
            # - number: 50 (fetch a large list to allow robust planning and avoid duplicates)
            url = "https://api.spoonacular.com/recipes/complexSearch"
            params = {
                "apiKey": self.api_key,
                "type": spoonacular_type,
                "diet": "dairyFree",
                "cuisine": "Mediterranean,Italian,Greek,Spanish,French",
                "addRecipeInformation": "true",
                "addRecipeNutrition": "true",
                "number": 50
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            recipes = []
            for item in results:
                recipes.append(self._parse_spoonacular_recipe(item, meal_type))
                
            if not recipes:
                print(f"[Client] Warning: Spoonacular returned 0 results for {meal_type}. Falling back to mock data.")
                return self._get_mock_recipes(meal_type)
                
            return recipes
            
        except Exception as e:
            print(f"[Client] Error fetching from Spoonacular API: {e}. Falling back to mock data.", flush=True)
            return self._get_mock_recipes(meal_type)

    def _parse_spoonacular_recipe(self, data: Dict[str, Any], meal_type: str) -> Recipe:
        """Parses a single recipe dictionary from the Spoonacular API response."""
        recipe_id = str(data.get("id"))
        title = data.get("title", "Unnamed Recipe")
        servings = data.get("servings", 2)
        source_url = data.get("sourceUrl", "")
        
        # Get Cuisines
        cuisines = data.get("cuisines", [])
        cuisine = cuisines[0] if cuisines else "Mediterranean"
        
        # Extract calories
        calories = 0.0
        nutrition = data.get("nutrition", {})
        nutrients = nutrition.get("nutrients", [])
        for nut in nutrients:
            if nut.get("name") == "Calories":
                calories = float(nut.get("amount", 0.0))
                break
                
        # Parse ingredients
        ingredients = []
        extended_ingredients = data.get("extendedIngredients", [])
        for ing in extended_ingredients:
            name = ing.get("nameClean") or ing.get("name", "")
            amount = float(ing.get("amount", 0.0))
            unit = ing.get("unit", "")
            aisle = ing.get("aisle", "")
            
            # Map Spoonacular aisle to our categories
            category = self._map_aisle_to_category(aisle, name)
            
            if name:
                ingredients.append(Ingredient(
                    name=name.lower(),
                    amount=amount,
                    unit=unit,
                    category=category
                ))
                
        return Recipe(
            id=recipe_id,
            title=title,
            calories=calories if calories > 0 else 400.0,  # Fallback calories
            servings=servings,
            cuisine=cuisine,
            meal_type=meal_type,
            ingredients=ingredients,
            source_url=source_url
        )

    def _map_aisle_to_category(self, aisle: str, name: str) -> str:
        """Maps Spoonacular aisle/categories or ingredient names to our standard grocery categories."""
        name = name.lower()
        aisle = aisle.lower() if aisle else ""
        
        # Check Dairy Alternatives first (lactose intolerance rules)
        dairy_alts = ["almond milk", "coconut milk", "soy milk", "oat milk", "dairy-free", "vegan cheese", "margarine", "coconut yogurt"]
        if any(alt in name for alt in dairy_alts):
            return "dairy alternatives"
            
        # Category checks
        if "produce" in aisle or "vegetables" in aisle or "fruit" in aisle:
            return "vegetables"
        elif "meat" in aisle or "seafood" in aisle or "poultry" in aisle or "fish" in aisle:
            return "proteins"
        elif "pantry" in aisle or "spices" in aisle or "oil" in aisle or "sauces" in aisle or "baking" in aisle or "canned" in aisle:
            return "pantry staples"
        elif "milk" in aisle or "cheese" in aisle or "dairy" in aisle:
            # Fallback check for dairy just in case, but since we are dairy-free, standard dairy should map to alternatives or pantry
            return "dairy alternatives"
        else:
            # Fallback keyword checks
            proteins_kw = ["chicken", "beef", "turkey", "pork", "salmon", "tuna", "cod", "shrimp", "tofu", "egg", "lamb"]
            veggies_kw = ["spinach", "tomato", "cucumber", "onion", "garlic", "pepper", "zucchini", "kale", "broccoli", "asparagus", "lemon", "avocado", "parsley", "basil", "dill", "herb"]
            pantry_kw = ["oil", "vinegar", "rice", "pasta", "flour", "sugar", "salt", "pepper", "broth", "chickpea", "bean", "lentil", "honey", "maple", "mustard"]
            
            if any(p in name for p in proteins_kw):
                return "proteins"
            elif any(v in name for v in veggies_kw):
                return "vegetables"
            elif any(pa in name for pa in pantry_kw):
                return "pantry staples"
            return "others"

    def _get_mock_recipes(self, meal_type: str) -> List[Recipe]:
        """Provides high-quality mock recipes for offline/no-key usage."""
        if meal_type == "breakfast":
            return [
                Recipe(
                    id="mock_b1", title="Mediterranean Avocado Toast", calories=350.0, servings=2, cuisine="Mediterranean", meal_type="breakfast",
                    source_url="https://example.com/recipes/avocado-toast",
                    ingredients=[
                        Ingredient("avocado", 1.0, "whole", "vegetables"),
                        Ingredient("sourdough bread", 2.0, "slice", "pantry staples"),
                        Ingredient("cherry tomatoes", 5.0, "whole", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples"),
                        Ingredient("salt and pepper", 1.0, "pinch", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b2", title="Spinach and Tomato Scrambled Eggs", calories=290.0, servings=2, cuisine="Mediterranean", meal_type="breakfast",
                    source_url="https://example.com/recipes/spinach-eggs",
                    ingredients=[
                        Ingredient("egg", 4.0, "whole", "proteins"),
                        Ingredient("spinach", 2.0, "cup", "vegetables"),
                        Ingredient("cherry tomatoes", 6.0, "whole", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b3", title="Almond Milk Oatmeal with Berries", calories=320.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/berry-oatmeal",
                    ingredients=[
                        Ingredient("rolled oats", 1.0, "cup", "pantry staples"),
                        Ingredient("almond milk", 2.0, "cup", "dairy alternatives"),
                        Ingredient("blueberries", 0.5, "cup", "vegetables"),
                        Ingredient("honey", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b4", title="Chia Seed Pudding with Coconut Milk", calories=250.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/chia-pudding",
                    ingredients=[
                        Ingredient("chia seeds", 0.25, "cup", "pantry staples"),
                        Ingredient("coconut milk", 1.0, "cup", "dairy alternatives"),
                        Ingredient("maple syrup", 1.0, "tbsp", "pantry staples"),
                        Ingredient("strawberries", 4.0, "sliced", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_b5", title="Hummus and Cucumber Toast", calories=300.0, servings=2, cuisine="Mediterranean", meal_type="breakfast",
                    source_url="https://example.com/recipes/hummus-toast",
                    ingredients=[
                        Ingredient("hummus", 4.0, "tbsp", "pantry staples"),
                        Ingredient("whole wheat bread", 2.0, "slice", "pantry staples"),
                        Ingredient("cucumber", 0.5, "sliced", "vegetables"),
                        Ingredient("olive oil", 0.5, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b6", title="Smoked Salmon and Dill Scramble", calories=360.0, servings=2, cuisine="European", meal_type="breakfast",
                    source_url="https://example.com/recipes/salmon-scramble",
                    ingredients=[
                        Ingredient("egg", 4.0, "whole", "proteins"),
                        Ingredient("smoked salmon", 100.0, "grams", "proteins"),
                        Ingredient("fresh dill", 1.0, "tbsp", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b7", title="Quinoa Breakfast Bowl", calories=380.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/quinoa-bowl",
                    ingredients=[
                        Ingredient("quinoa", 0.75, "cup", "pantry staples"),
                        Ingredient("almond milk", 1.5, "cup", "dairy alternatives"),
                        Ingredient("banana", 1.0, "sliced", "vegetables"),
                        Ingredient("walnuts", 2.0, "tbsp", "pantry staples"),
                        Ingredient("cinnamon", 0.5, "tsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b8", title="Green Smoothie Bowl", calories=310.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/green-smoothie",
                    ingredients=[
                        Ingredient("banana", 1.0, "whole", "vegetables"),
                        Ingredient("spinach", 2.0, "cup", "vegetables"),
                        Ingredient("almond milk", 1.0, "cup", "dairy alternatives"),
                        Ingredient("chia seeds", 1.0, "tbsp", "pantry staples"),
                        Ingredient("granola", 0.5, "cup", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b9", title="Greek Tomato and Herb Frittata", calories=280.0, servings=2, cuisine="Greek", meal_type="breakfast",
                    source_url="https://example.com/recipes/greek-frittata",
                    ingredients=[
                        Ingredient("egg", 5.0, "whole", "proteins"),
                        Ingredient("roma tomatoes", 2.0, "chopped", "vegetables"),
                        Ingredient("oregano", 1.0, "tsp", "pantry staples"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples"),
                        Ingredient("green onions", 2.0, "sliced", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_b10", title="Olive Oil Fried Eggs with Asparagus", calories=290.0, servings=2, cuisine="Mediterranean", meal_type="breakfast",
                    source_url="https://example.com/recipes/eggs-asparagus",
                    ingredients=[
                        Ingredient("egg", 4.0, "whole", "proteins"),
                        Ingredient("asparagus spears", 10.0, "whole", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("garlic", 1.0, "clove", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_b11", title="Almond Butter and Banana Toast", calories=400.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/banana-toast",
                    ingredients=[
                        Ingredient("almond butter", 2.0, "tbsp", "dairy alternatives"),
                        Ingredient("sourdough bread", 2.0, "slice", "pantry staples"),
                        Ingredient("banana", 1.0, "sliced", "vegetables"),
                        Ingredient("cinnamon", 0.25, "tsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b12", title="Fruit and Nut Oatmeal", calories=340.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/fruit-oatmeal",
                    ingredients=[
                        Ingredient("rolled oats", 1.0, "cup", "pantry staples"),
                        Ingredient("water", 2.0, "cup", "pantry staples"),
                        Ingredient("almonds", 0.25, "cup", "pantry staples"),
                        Ingredient("raisins", 2.0, "tbsp", "pantry staples"),
                        Ingredient("apple", 0.5, "sliced", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_b13", title="Zucchini and Basil Scramble", calories=275.0, servings=2, cuisine="Italian", meal_type="breakfast",
                    source_url="https://example.com/recipes/zucchini-scramble",
                    ingredients=[
                        Ingredient("egg", 4.0, "whole", "proteins"),
                        Ingredient("zucchini", 1.0, "shredded", "vegetables"),
                        Ingredient("fresh basil", 5.0, "leaves", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_b14", title="Olive Tapenade Sourdough Slice", calories=270.0, servings=2, cuisine="Mediterranean", meal_type="breakfast",
                    source_url="https://example.com/recipes/tapenade-sourdough",
                    ingredients=[
                        Ingredient("sourdough bread", 2.0, "slice", "pantry staples"),
                        Ingredient("olive tapenade", 3.0, "tbsp", "pantry staples"),
                        Ingredient("cherry tomatoes", 4.0, "sliced", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_b15", title="Blueberry Almond Flour Pancakes", calories=420.0, servings=2, cuisine="Western", meal_type="breakfast",
                    source_url="https://example.com/recipes/blueberry-pancakes",
                    ingredients=[
                        Ingredient("almond flour", 1.0, "cup", "pantry staples"),
                        Ingredient("egg", 2.0, "whole", "proteins"),
                        Ingredient("almond milk", 0.25, "cup", "dairy alternatives"),
                        Ingredient("blueberries", 0.5, "cup", "vegetables"),
                        Ingredient("maple syrup", 2.0, "tbsp", "pantry staples")
                    ]
                )
            ]
            
        elif meal_type == "lunch":
            return [
                Recipe(
                    id="mock_l1", title="Mediterranean Chickpea Salad", calories=450.0, servings=2, cuisine="Mediterranean", meal_type="lunch",
                    source_url="https://example.com/recipes/chickpea-salad",
                    ingredients=[
                        Ingredient("canned chickpeas", 1.5, "can", "pantry staples"),
                        Ingredient("cucumber", 1.0, "chopped", "vegetables"),
                        Ingredient("red onion", 0.5, "chopped", "vegetables"),
                        Ingredient("parsley", 0.25, "cup", "vegetables"),
                        Ingredient("lemon juice", 2.0, "tbsp", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("salt and pepper", 1.0, "pinch", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l2", title="Tuna and White Bean Salad", calories=420.0, servings=2, cuisine="Italian", meal_type="lunch",
                    source_url="https://example.com/recipes/tuna-bean-salad",
                    ingredients=[
                        Ingredient("canned tuna", 2.0, "can", "proteins"),
                        Ingredient("cannellini beans", 1.0, "can", "pantry staples"),
                        Ingredient("red onion", 0.5, "sliced", "vegetables"),
                        Ingredient("arugula", 2.0, "cup", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("lemon juice", 1.5, "tbsp", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_l3", title="Grilled Chicken Salad Wrap", calories=490.0, servings=2, cuisine="Western", meal_type="lunch",
                    source_url="https://example.com/recipes/chicken-wrap",
                    ingredients=[
                        Ingredient("chicken breast", 200.0, "grams", "proteins"),
                        Ingredient("lactose-free wrap", 2.0, "whole", "pantry staples"),
                        Ingredient("hummus", 4.0, "tbsp", "pantry staples"),
                        Ingredient("cucumber", 0.5, "sliced", "vegetables"),
                        Ingredient("tomato", 1.0, "sliced", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l4", title="Roasted Quinoa and Veg Bowl", calories=430.0, servings=2, cuisine="Mediterranean", meal_type="lunch",
                    source_url="https://example.com/recipes/roasted-quinoa",
                    ingredients=[
                        Ingredient("quinoa", 1.0, "cup", "pantry staples"),
                        Ingredient("bell peppers", 1.0, "chopped", "vegetables"),
                        Ingredient("zucchini", 1.0, "chopped", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("lemon juice", 1.0, "tbsp", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_l5", title="Lentil Soup with Spinach", calories=380.0, servings=2, cuisine="European", meal_type="lunch",
                    source_url="https://example.com/recipes/lentil-soup",
                    ingredients=[
                        Ingredient("brown lentils", 1.0, "cup", "pantry staples"),
                        Ingredient("carrots", 2.0, "chopped", "vegetables"),
                        Ingredient("celery stalks", 2.0, "chopped", "vegetables"),
                        Ingredient("spinach", 2.0, "cup", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("vegetable broth", 4.0, "cup", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l6", title="Tomato Basil Gazpacho", calories=320.0, servings=2, cuisine="Spanish", meal_type="lunch",
                    source_url="https://example.com/recipes/gazpacho",
                    ingredients=[
                        Ingredient("tomatoes", 4.0, "ripe", "vegetables"),
                        Ingredient("cucumber", 1.0, "peeled", "vegetables"),
                        Ingredient("bell pepper", 1.0, "chopped", "vegetables"),
                        Ingredient("garlic", 2.0, "clove", "vegetables"),
                        Ingredient("olive oil", 3.0, "tbsp", "pantry staples"),
                        Ingredient("sourdough bread", 2.0, "slice", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l7", title="Turkey and Avocado Salad", calories=460.0, servings=2, cuisine="Western", meal_type="lunch",
                    source_url="https://example.com/recipes/turkey-salad",
                    ingredients=[
                        Ingredient("turkey breast", 150.0, "grams", "proteins"),
                        Ingredient("avocado", 1.0, "sliced", "vegetables"),
                        Ingredient("mixed greens", 4.0, "cup", "vegetables"),
                        Ingredient("cherry tomatoes", 8.0, "whole", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("balsamic vinegar", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l8", title="Mediterranean Falafel Quinoa Bowl", calories=520.0, servings=2, cuisine="Mediterranean", meal_type="lunch",
                    source_url="https://example.com/recipes/falafel-quinoa",
                    ingredients=[
                        Ingredient("quinoa", 0.75, "cup", "pantry staples"),
                        Ingredient("falafel", 6.0, "pieces", "proteins"),
                        Ingredient("cucumber", 0.5, "chopped", "vegetables"),
                        Ingredient("black olives", 10.0, "whole", "vegetables"),
                        Ingredient("hummus", 4.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l9", title="Lemon Shrimp and Avocado Salad", calories=410.0, servings=2, cuisine="Western", meal_type="lunch",
                    source_url="https://example.com/recipes/shrimp-avocado-salad",
                    ingredients=[
                        Ingredient("shrimp", 200.0, "grams", "proteins"),
                        Ingredient("avocado", 1.0, "sliced", "vegetables"),
                        Ingredient("butter lettuce", 4.0, "cup", "vegetables"),
                        Ingredient("lemon juice", 2.0, "tbsp", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l10", title="Tuscan White Bean and Kale Soup", calories=350.0, servings=2, cuisine="Italian", meal_type="lunch",
                    source_url="https://example.com/recipes/tuscan-soup",
                    ingredients=[
                        Ingredient("cannellini beans", 1.5, "can", "pantry staples"),
                        Ingredient("kale", 3.0, "cup", "vegetables"),
                        Ingredient("carrots", 1.0, "chopped", "vegetables"),
                        Ingredient("vegetable broth", 4.0, "cup", "pantry staples"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l11", title="Arugula Salad with Roasted Tomatoes", calories=390.0, servings=2, cuisine="Italian", meal_type="lunch",
                    source_url="https://example.com/recipes/roasted-tomato-salad",
                    ingredients=[
                        Ingredient("brown lentils", 1.0, "cup", "pantry staples"),
                        Ingredient("cherry tomatoes", 1.0, "pint", "vegetables"),
                        Ingredient("arugula", 3.0, "cup", "vegetables"),
                        Ingredient("balsamic glaze", 1.5, "tbsp", "pantry staples"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l12", title="Cold Salmon Spinach Salad", calories=480.0, servings=2, cuisine="European", meal_type="lunch",
                    source_url="https://example.com/recipes/salmon-spinach-salad",
                    ingredients=[
                        Ingredient("baked salmon", 180.0, "grams", "proteins"),
                        Ingredient("baby spinach", 4.0, "cup", "vegetables"),
                        Ingredient("walnuts", 0.25, "cup", "pantry staples"),
                        Ingredient("cucumber", 0.5, "chopped", "vegetables"),
                        Ingredient("lemon juice", 1.5, "tbsp", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l13", title="Mediterranean Herb Potato Salad", calories=360.0, servings=2, cuisine="French", meal_type="lunch",
                    source_url="https://example.com/recipes/herb-potato-salad",
                    ingredients=[
                        Ingredient("potatoes", 4.0, "medium", "vegetables"),
                        Ingredient("red onion", 0.5, "diced", "vegetables"),
                        Ingredient("capers", 2.0, "tbsp", "pantry staples"),
                        Ingredient("parsley", 0.25, "cup", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("dijon mustard", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_l14", title="Quinoa Stuffed Bell Peppers", calories=410.0, servings=2, cuisine="Mediterranean", meal_type="lunch",
                    source_url="https://example.com/recipes/stuffed-peppers",
                    ingredients=[
                        Ingredient("bell peppers", 2.0, "whole", "vegetables"),
                        Ingredient("quinoa", 0.5, "cup", "pantry staples"),
                        Ingredient("black beans", 0.5, "can", "pantry staples"),
                        Ingredient("corn", 0.5, "cup", "vegetables"),
                        Ingredient("cilantro", 2.0, "tbsp", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_l15", title="White Bean Dip with Fresh Crudités", calories=330.0, servings=2, cuisine="Mediterranean", meal_type="lunch",
                    source_url="https://example.com/recipes/bean-dip",
                    ingredients=[
                        Ingredient("cannellini beans", 1.0, "can", "pantry staples"),
                        Ingredient("garlic", 1.0, "clove", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("carrots", 2.0, "sticks", "vegetables"),
                        Ingredient("cucumber", 1.0, "sliced", "vegetables")
                    ]
                )
            ]
            
        else: # dinner
            return [
                Recipe(
                    id="mock_d1", title="Baked Lemon Herb Salmon", calories=550.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/baked-salmon",
                    ingredients=[
                        Ingredient("salmon fillet", 300.0, "grams", "proteins"),
                        Ingredient("lemon", 1.0, "sliced", "vegetables"),
                        Ingredient("fresh dill", 2.0, "tbsp", "vegetables"),
                        Ingredient("garlic", 2.0, "cloves", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("broccoli florets", 2.0, "cups", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d2", title="Grilled Rosemary Chicken Breast", calories=480.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/rosemary-chicken",
                    ingredients=[
                        Ingredient("chicken breast", 350.0, "grams", "proteins"),
                        Ingredient("fresh rosemary", 2.0, "sprigs", "vegetables"),
                        Ingredient("garlic", 3.0, "cloves", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("asparagus spears", 12.0, "whole", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d3", title="Garlic Herb Shrimp Pasta", calories=620.0, servings=2, cuisine="Italian", meal_type="dinner",
                    source_url="https://example.com/recipes/shrimp-pasta",
                    ingredients=[
                        Ingredient("gluten-free pasta", 150.0, "grams", "pantry staples"),
                        Ingredient("shrimp", 250.0, "grams", "proteins"),
                        Ingredient("garlic", 4.0, "cloves", "vegetables"),
                        Ingredient("cherry tomatoes", 1.0, "cup", "vegetables"),
                        Ingredient("olive oil", 2.5, "tbsp", "pantry staples"),
                        Ingredient("parsley", 2.0, "tbsp", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d4", title="Mediterranean Baked Cod", calories=450.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/baked-cod",
                    ingredients=[
                        Ingredient("cod fillet", 300.0, "grams", "proteins"),
                        Ingredient("cherry tomatoes", 1.0, "cup", "vegetables"),
                        Ingredient("kalamata olives", 10.0, "sliced", "vegetables"),
                        Ingredient("capers", 1.0, "tbsp", "pantry staples"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("zucchini", 1.0, "sliced", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d5", title="Beef and Herb Sauté with Potatoes", calories=580.0, servings=2, cuisine="European", meal_type="dinner",
                    source_url="https://example.com/recipes/beef-potatoes",
                    ingredients=[
                        Ingredient("beef sirloin", 300.0, "grams", "proteins"),
                        Ingredient("potatoes", 2.0, "cubed", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("fresh thyme", 1.0, "tsp", "vegetables"),
                        Ingredient("garlic", 2.0, "cloves", "vegetables"),
                        Ingredient("green beans", 1.5, "cup", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d6", title="Roasted Chicken Thighs with Sweet Potatoes", calories=610.0, servings=2, cuisine="Western", meal_type="dinner",
                    source_url="https://example.com/recipes/roasted-chicken-thighs",
                    ingredients=[
                        Ingredient("chicken thighs", 4.0, "whole", "proteins"),
                        Ingredient("sweet potatoes", 2.0, "cubed", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("garlic", 3.0, "cloves", "vegetables"),
                        Ingredient("dried thyme", 1.0, "tsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d7", title="Pork Loin with Apple and Green Beans", calories=520.0, servings=2, cuisine="European", meal_type="dinner",
                    source_url="https://example.com/recipes/pork-loin",
                    ingredients=[
                        Ingredient("pork loin", 300.0, "grams", "proteins"),
                        Ingredient("apples", 1.0, "sliced", "vegetables"),
                        Ingredient("green beans", 2.0, "cups", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d8", title="Turkey Meatballs with Zucchini Noodles", calories=490.0, servings=2, cuisine="Italian", meal_type="dinner",
                    source_url="https://example.com/recipes/turkey-meatballs",
                    ingredients=[
                        Ingredient("ground turkey", 300.0, "grams", "proteins"),
                        Ingredient("breadcrumbs", 0.5, "cup", "pantry staples"),
                        Ingredient("egg", 1.0, "whole", "proteins"),
                        Ingredient("marinara sauce", 1.5, "cup", "pantry staples"),
                        Ingredient("zucchini", 2.0, "spiralized", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d9", title="Baked Seabass with Fennel", calories=440.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/baked-seabass",
                    ingredients=[
                        Ingredient("seabass fillet", 300.0, "grams", "proteins"),
                        Ingredient("fennel bulb", 1.0, "sliced", "vegetables"),
                        Ingredient("cherry tomatoes", 1.0, "cup", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("fresh thyme", 1.0, "tsp", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d10", title="Grilled Lamb Chops with Potatoes", calories=650.0, servings=2, cuisine="Greek", meal_type="dinner",
                    source_url="https://example.com/recipes/lamb-chops",
                    ingredients=[
                        Ingredient("lamb chops", 4.0, "whole", "proteins"),
                        Ingredient("potatoes", 2.0, "roasted", "vegetables"),
                        Ingredient("fresh mint", 2.0, "tbsp", "vegetables"),
                        Ingredient("garlic", 2.0, "cloves", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d11", title="Chickpea and Vegetable Mediterranean Stew", calories=410.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/chickpea-stew",
                    ingredients=[
                        Ingredient("canned chickpeas", 1.5, "can", "pantry staples"),
                        Ingredient("zucchini", 1.0, "sliced", "vegetables"),
                        Ingredient("canned tomatoes", 1.0, "can", "pantry staples"),
                        Ingredient("carrots", 2.0, "chopped", "vegetables"),
                        Ingredient("cumin", 1.0, "tsp", "pantry staples"),
                        Ingredient("vegetable broth", 2.0, "cups", "pantry staples"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d12", title="Turkey Breast with Rosemary Potatoes", calories=540.0, servings=2, cuisine="Western", meal_type="dinner",
                    source_url="https://example.com/recipes/turkey-potatoes",
                    ingredients=[
                        Ingredient("turkey breast", 300.0, "grams", "proteins"),
                        Ingredient("potatoes", 3.0, "cubed", "vegetables"),
                        Ingredient("olive oil", 2.0, "tbsp", "pantry staples"),
                        Ingredient("fresh rosemary", 2.0, "tbsp", "vegetables"),
                        Ingredient("garlic", 2.0, "cloves", "vegetables")
                    ]
                ),
                Recipe(
                    id="mock_d13", title="Lemon Grilled Tuna Steak", calories=480.0, servings=2, cuisine="Mediterranean", meal_type="dinner",
                    source_url="https://example.com/recipes/tuna-steak",
                    ingredients=[
                        Ingredient("tuna steak", 300.0, "grams", "proteins"),
                        Ingredient("green beans", 2.0, "cups", "vegetables"),
                        Ingredient("lemon", 1.0, "zested and juiced", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples"),
                        Ingredient("oregano", 0.5, "tsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d14", title="Mediterranean Lamb Quinoa Bowl", calories=590.0, servings=2, cuisine="Greek", meal_type="dinner",
                    source_url="https://example.com/recipes/lamb-quinoa",
                    ingredients=[
                        Ingredient("ground lamb", 250.0, "grams", "proteins"),
                        Ingredient("quinoa", 1.0, "cup", "pantry staples"),
                        Ingredient("cucumber", 0.5, "chopped", "vegetables"),
                        Ingredient("red onion", 0.5, "diced", "vegetables"),
                        Ingredient("parsley", 0.25, "cup", "vegetables"),
                        Ingredient("olive oil", 1.0, "tbsp", "pantry staples")
                    ]
                ),
                Recipe(
                    id="mock_d15", title="Pork Chop with Braised Cabbage", calories=530.0, servings=2, cuisine="Western", meal_type="dinner",
                    source_url="https://example.com/recipes/pork-cabbage",
                    ingredients=[
                        Ingredient("pork chops", 2.0, "whole", "proteins"),
                        Ingredient("red cabbage", 0.5, "shredded", "vegetables"),
                        Ingredient("apple cider vinegar", 2.0, "tbsp", "pantry staples"),
                        Ingredient("apple", 0.5, "diced", "vegetables"),
                        Ingredient("olive oil", 1.5, "tbsp", "pantry staples")
                    ]
                )
            ]
        return []
