import re
from typing import Dict, List, Any
from recipe_client import Recipe, Ingredient

# Categorization lists for simple rule-based fallback classification
VEGETABLES_KEYWORDS = [
    "avocado", "spinach", "tomato", "cucumber", "onion", "garlic", "pepper", "zucchini", "kale", 
    "broccoli", "asparagus", "lemon", "lime", "parsley", "basil", "dill", "herb", "cilantro", "oregano",
    "thyme", "rosemary", "mint", "cabbage", "carrot", "celery", "arugula", "lettuce", "greens", "fennel",
    "apple", "blueberry", "strawberry", "banana", "raisins", "fruit", "berries", "ginger"
]

PROTEINS_KEYWORDS = [
    "chicken", "beef", "turkey", "pork", "salmon", "tuna", "cod", "shrimp", "seabass", "lamb", "egg",
    "tofu", "tempeh", "ham", "bacon", "steak", "fillet", "meatballs"
]

PANTRY_KEYWORDS = [
    "oil", "vinegar", "rice", "pasta", "flour", "sugar", "salt", "pepper", "broth", "chickpea", 
    "bean", "lentil", "honey", "maple", "mustard", "tapenade", "hummus", "wrap", "tortilla",
    "chia", "oat", "oats", "seed", "nuts", "walnuts", "almonds", "cinnamon", "capers", "olives",
    "marinara", "sauce", "breadcrumbs", "yeast", "glaze"
]

DAIRY_ALTS_KEYWORDS = [
    "almond milk", "coconut milk", "soy milk", "oat milk", "rice milk", "dairy-free", "dairy free",
    "vegan cheese", "vegan butter", "coconut yogurt", "coconut cream", "almond butter", "margarine"
]

def clean_ingredient_name(name: str) -> str:
    """Normalizes ingredient names by lowering case, removing descriptors and plural suffixes."""
    name = name.lower().strip()
    
    # Remove common descriptors that cause duplicate matches
    descriptors = [
        r'\bextra virgin\b', r'\bvirgin\b', r'\borganic\b', r'\bfreshly\b', r'\bfresh\b',
        r'\bripe\b', r'\bchopped\b', r'\bsliced\b', r'\bminced\b', r'\bdiced\b',
        r'\bgrated\b', r'\bshredded\b', r'\bdried\b', r'\bground\b', r'\bpeeled\b',
        r'\bcooked\b', r'\bbaked\b', r'\bcanned\b', r'\bwhole\b', r'\bslices\b',
        r'\bpieces\b', r'\bcubes\b', r'\bcubed\b', r'\bfillet\b', r'\bfillets\b',
        r'\bspears\b', r'\bcloves\b', r'\bclove\b', r'\bheads\b', r'\bhead\b',
        r'\bsprigs\b', r'\bsprig\b', r'\bripe\b'
    ]
    
    for pattern in descriptors:
        name = re.sub(pattern, '', name)
        
    # Replace multiple spaces with a single space and strip
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Basic singularization for standard ingredients
    singulars = {
        "tomatoes": "tomato",
        "blueberries": "blueberry",
        "strawberries": "strawberry",
        "apples": "apple",
        "potatoes": "potato",
        "onions": "onion",
        "carrots": "carrot",
        "bell peppers": "bell pepper",
        "peppers": "bell pepper",
        "eggs": "egg",
        "cloves": "garlic",
        "chickpeas": "chickpea",
        "beans": "bean",
        "lentils": "lentil",
        "walnuts": "walnut",
        "almonds": "almond",
        "bananas": "banana",
        "lemons": "lemon",
        "limes": "lime",
        "olives": "olive"
    }
    
    for plural, singular in singulars.items():
        if name.endswith(plural):
            # Replace the plural part
            name = re.sub(re.escape(plural) + r'$', singular, name)
            break
            
    return name

def classify_ingredient(name: str, current_category: str) -> str:
    """Classifies an ingredient into a category. Uses the client category as a primary hint."""
    # If the category is already set to something specific (not 'others'), trust it
    if current_category in ["vegetables", "proteins", "pantry staples", "dairy alternatives"]:
        return current_category
        
    name = name.lower()
    
    # Check dairy alternatives first (high priority for safety)
    if any(kw in name for kw in DAIRY_ALTS_KEYWORDS):
        return "dairy alternatives"
    elif any(kw in name for kw in PROTEINS_KEYWORDS):
        return "proteins"
    elif any(kw in name for kw in VEGETABLES_KEYWORDS):
        return "vegetables"
    elif any(kw in name for kw in PANTRY_KEYWORDS):
        return "pantry staples"
        
    return "others"

class GroceryBuilder:
    """Orchestrates grocery list consolidation and categorization."""
    
    def build_grocery_list(self, plan: Dict[str, Dict[str, Recipe]]) -> Dict[str, List[str]]:
        """Consolidates ingredients from a weekly meal plan and categorizes them."""
        # Aggregation structure: { clean_name: { unit: amount } }
        # And we store the category of each ingredient: { clean_name: category }
        aggregated: Dict[str, Dict[str, float]] = {}
        categories: Dict[str, str] = {}
        
        # Iterate over all meals in the plan
        for day, meals in plan.items():
            for meal_type, recipe in meals.items():
                for ing in recipe.ingredients:
                    clean_name = clean_ingredient_name(ing.name)
                    unit = ing.unit.lower().strip()
                    
                    # Normalize empty unit to 'unitless' / 'whole'
                    if not unit:
                        unit = "whole"
                        
                    # Standardize some units
                    if unit in ["tablespoon", "tablespoons", "tbsp."]:
                        unit = "tbsp"
                    elif unit in ["teaspoon", "teaspoons", "tsp."]:
                        unit = "tsp"
                    elif unit in ["cup", "cups"]:
                        unit = "cup"
                    elif unit in ["gram", "grams", "g."]:
                        unit = "grams"
                    elif unit in ["can", "cans"]:
                        unit = "can"
                    elif unit in ["clove", "cloves"]:
                        unit = "clove"
                        
                    # Add to aggregate dictionary
                    if clean_name not in aggregated:
                        aggregated[clean_name] = {}
                    
                    aggregated[clean_name][unit] = aggregated[clean_name].get(unit, 0.0) + ing.amount
                    
                    # Classify category
                    raw_cat = classify_ingredient(clean_name, ing.category)
                    categories[clean_name] = raw_cat
                    
        # Group consolidated items into categories
        categorized_list: Dict[str, List[str]] = {
            "vegetables": [],
            "proteins": [],
            "pantry staples": [],
            "dairy alternatives": [],
            "others": []
        }
        
        for name, units in sorted(aggregated.items()):
            category = categories[name]
            
            # Format quantity string (e.g., "2.0 cups and 1.0 tbsp olive oil")
            qty_parts = []
            for unit, amt in sorted(units.items()):
                # Format floats cleanly (e.g., 2.0 -> 2, 2.5 -> 2.5)
                amt_str = f"{int(amt)}" if amt.is_integer() else f"{amt:.2f}"
                
                # Singular/plural logic for display
                if amt == 1 and unit != "whole":
                    qty_parts.append(f"{amt_str} {unit}")
                elif unit == "whole":
                    qty_parts.append(amt_str)
                else:
                    qty_parts.append(f"{amt_str} {unit}s" if not unit.endswith("s") and unit not in ["tsp", "tbsp", "grams"] else f"{amt_str} {unit}")
                    
            qty_str = " + ".join(qty_parts)
            formatted_line = f"{qty_str} {name}" if qty_str else name
            
            categorized_list[category].append(formatted_line)
            
        return categorized_list
