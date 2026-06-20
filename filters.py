import re
from typing import List
from recipe_client import Recipe, Ingredient

# Forbidden cuisines (strictly avoid Asian)
FORBIDDEN_CUISINES = {
    "asian", "chinese", "japanese", "korean", "thai", "vietnamese", 
    "indian", "nepalese", "tibetan", "filipino", "malaysian"
}

# Dairy ingredients to strictly avoid
DAIRY_KEYWORDS = {
    "milk", "butter", "cheese", "cream", "yogurt", "ghee", "crayfish", # crayfish is not dairy, but let's stick to dairy
    "sour cream", "cream cheese", "mozzarella", "parmesan", "cheddar", 
    "feta", "ricotta", "mascarpone", "whey", "casein", "buttermilk"
}

# Allowed alternatives that are safe (must not be flagged as dairy)
DAIRY_ALTERNATIVES = {
    "almond milk", "coconut milk", "soy milk", "oat milk", "rice milk",
    "dairy-free", "dairy free", "vegan cheese", "vegan butter", 
    "coconut yogurt", "coconut cream", "almond butter", "margarine",
    "butter lettuce", "butter bean", "butternut squash"
}

def is_dairy_free(recipe: Recipe) -> bool:
    """Returns True if the recipe does not contain dairy products."""
    # Check title first
    title_lower = recipe.title.lower()
    for kw in DAIRY_KEYWORDS:
        # Check if the word is in the title
        if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
            # Check if it has a dairy alternative prefix
            has_alt = False
            for alt in DAIRY_ALTERNATIVES:
                if alt in title_lower:
                    has_alt = True
                    break
            if not has_alt:
                return False

    # Check each ingredient
    for ing in recipe.ingredients:
        ing_name = ing.name.lower()
        
        # If it explicitly maps to the 'dairy alternatives' category, it is safe
        if ing.category == "dairy alternatives":
            continue
            
        for kw in DAIRY_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', ing_name):
                # Verify if it is an alternative
                has_alt = False
                for alt in DAIRY_ALTERNATIVES:
                    if alt in ing_name:
                        has_alt = True
                        break
                if not has_alt:
                    return False
                    
    return True

def is_cuisine_allowed(recipe: Recipe) -> bool:
    """Returns True if the recipe cuisine is allowed (strictly avoids Asian)."""
    cuisine_lower = recipe.cuisine.lower()
    
    # Check if the cuisine matches any forbidden cuisine
    for forbidden in FORBIDDEN_CUISINES:
        if forbidden in cuisine_lower:
            return False
            
    # Check the recipe title for forbidden cuisines, just in case
    title_lower = recipe.title.lower()
    for forbidden in FORBIDDEN_CUISINES:
        if re.search(r'\b' + re.escape(forbidden) + r'\b', title_lower):
            return False
            
    return True

def filter_recipes(recipes: List[Recipe]) -> List[Recipe]:
    """Applies all filters to a list of recipes and returns the valid ones."""
    filtered = []
    for recipe in recipes:
        if is_dairy_free(recipe) and is_cuisine_allowed(recipe):
            filtered.append(recipe)
        else:
            # Print a message indicating why a recipe was filtered
            reason = []
            if not is_dairy_free(recipe):
                reason.append("dairy content")
            if not is_cuisine_allowed(recipe):
                reason.append("asian/forbidden cuisine")
            print(f"[Filter] Excluded recipe: '{recipe.title}' (Cuisine: {recipe.cuisine}) due to: {', '.join(reason)}")
            
    return filtered
