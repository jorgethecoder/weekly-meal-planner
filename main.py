import argparse
import sys
from datetime import datetime
import config
from recipe_client import RecipeClient
from planner import MealPlanner
from storage import MealHistoryManager
from grocery import GroceryBuilder
from emailer import EmailManager

def print_text_summary(plan, grocery_list):
    """Prints a user-friendly text summary of the meal plan and grocery list to console."""
    print("\n" + "=" * 50)
    print("📅 WEEKLY MEAL PLAN SUMMARY")
    print("=" * 50)
    for day, meals in plan.items():
        print(f"\n[{day}]")
        print(f"  🍳 Breakfast: {meals['breakfast'].title} (~{int(meals['breakfast'].calories)} kcal)")
        print(f"  🥗 Lunch:     {meals['lunch'].title} (~{int(meals['lunch'].calories)} kcal)")
        print(f"  🍽️ Dinner:    {meals['dinner'].title} (~{int(meals['dinner'].calories)} kcal)")
        
    print("\n" + "=" * 50)
    print("🛒 CONSOLIDATED GROCERY LIST")
    print("=" * 50)
    category_icons = {
        "vegetables": "🥬 Vegetables & Fruits",
        "proteins": "🥩 Proteins (Meat & Fish)",
        "pantry staples": "🧂 Pantry Staples & Grains",
        "dairy alternatives": "🥛 Dairy & Lactose Alternatives",
        "others": "📦 Others"
    }
    for category, items in grocery_list.items():
        if items:
            print(f"\n{category_icons.get(category, category.upper())}:")
            for item in items:
                print(f"  [ ] {item}")
    print("\n" + "=" * 50)

def main():
    parser = argparse.ArgumentParser(description="Automated Weekly Meal Planner & Grocery Email System")
    parser.add_argument(
        "--local-only", 
        action="store_true", 
        help="Skip sending emails, write rendered HTML to 'meal_plan.html', and print summary to console"
    )
    args = parser.parse_args()

    print(f"--- Weekly Meal Planner Execution ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 1. Initialize Clients and Managers
    client = RecipeClient()
    planner = MealPlanner(client)
    history_manager = MealHistoryManager()
    grocery_builder = GroceryBuilder()
    emailer = EmailManager()

    # Determine if we should fallback to local-only execution
    local_only = args.local_only
    if not local_only:
        # Check if email configuration exists. If not, auto-fallback to local-only with a message
        if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
            print("[System] Gmail credentials not detected. Automatically falling back to local-only mode.")
            print("[System] To enable email delivery, configure GMAIL_USER and GMAIL_APP_PASSWORD in a .env file.")
            local_only = True

    # 2. Load History
    print("[System] Loading history to prevent recipe repetitions...")
    history_titles = history_manager.get_recent_meal_titles()
    print(f"[System] Loaded {len(history_titles)} recent meal titles from history.")

    # 3. Generate Plan
    print("[System] Selecting meals and scaling ingredient quantities...")
    plan = planner.generate_plan(history_titles)
    print("[System] Weekly plan successfully generated and scaled for 2 adults (2500 kcal / 2000 kcal).")

    # 4. Build Grocery List
    print("[System] Consolidating ingredients and building grocery list...")
    grocery_list = grocery_builder.build_grocery_list(plan)
    print("[System] Grocery list built and categorized.")

    # 5. Save History & Prune Stale History
    print("[System] Saving newly planned meals to history...")
    history_manager.save_and_prune(plan)

    # 6. Deliver Output
    if local_only:
        print("[System] Generating local output HTML...")
        html_content = emailer.generate_html_content(plan, grocery_list)
        output_file = "meal_plan.html"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[System] Saved weekly HTML plan locally to: {output_file}")
        except Exception as e:
            print(f"[System] Failed to write local HTML: {e}", file=sys.stderr)
            
        print_text_summary(plan, grocery_list)
    else:
        print("[System] Sending weekly meal plan email...")
        try:
            emailer.send_weekly_email(plan, grocery_list)
        except Exception as e:
            print(f"[System] Failed to send email: {e}. Writing output to 'meal_plan.html' as fallback.", file=sys.stderr)
            html_content = emailer.generate_html_content(plan, grocery_list)
            with open("meal_plan.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("[System] Saved backup HTML plan locally to: meal_plan.html")
            sys.exit(1)

    print("[System] Meal planner execution completed successfully!")

if __name__ == "__main__":
    main()
