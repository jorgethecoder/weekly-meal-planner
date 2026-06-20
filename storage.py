import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Any
import config

class MealHistoryManager:
    """Manages history persistence in JSON and prunes entries older than 2 weeks."""
    
    def __init__(self, filepath: str = config.HISTORY_FILE):
        self.filepath = filepath
        
    def load_history(self) -> List[Dict[str, Any]]:
        """Loads all history records from the JSON file."""
        if not os.path.exists(self.filepath):
            return []
            
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception as e:
            print(f"[Storage] Error loading history from {self.filepath}: {e}. Starting fresh.")
            return []
            
    def get_recent_meal_titles(self) -> Set[str]:
        """Extracts a set of all recipe titles from the history to prevent repetition."""
        history = self.load_history()
        recent_titles: Set[str] = set()
        
        # We only care about history that hasn't been pruned
        # Let's prune first in memory to ensure we aren't loading stale data
        pruned_history = self._prune_history_records(history)
        
        for record in pruned_history:
            meals = record.get("meals", [])
            for meal in meals:
                recent_titles.add(meal)
                
        return recent_titles

    def save_and_prune(self, new_plan: Dict[str, Dict[str, Any]], execution_date: datetime = None) -> None:
        """Saves the new plan's meal titles to history and prunes items older than 2 weeks."""
        if execution_date is None:
            execution_date = datetime.now()
            
        # Extract titles from the new plan
        new_titles = []
        for day, meals in new_plan.items():
            for meal_type, recipe in meals.items():
                new_titles.append(recipe.title)
                
        # Load existing history
        history = self.load_history()
        
        # Create a new record
        new_record = {
            "date": execution_date.strftime("%Y-%m-%d"),
            "meals": new_titles
        }
        
        # Add to history
        history.append(new_record)
        
        # Prune records older than 14 days
        cleaned_history = self._prune_history_records(history, execution_date)
        
        # Write back to file
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_history, f, indent=2, ensure_ascii=False)
            print(f"[Storage] Saved meal history to '{self.filepath}'. Total stored weeks: {len(cleaned_history)}")
        except Exception as e:
            print(f"[Storage] Failed to save history to {self.filepath}: {e}")

    def _prune_history_records(self, history: List[Dict[str, Any]], reference_date: datetime = None) -> List[Dict[str, Any]]:
        """Filters out records that are older than 14 days relative to the reference date."""
        if reference_date is None:
            reference_date = datetime.now()
            
        pruned = []
        for record in history:
            date_str = record.get("date")
            try:
                record_date = datetime.strptime(date_str, "%Y-%m-%d")
                # Check if the record is within the last 14 days (2 weeks)
                if reference_date - record_date <= timedelta(days=14):
                    pruned.append(record)
                else:
                    print(f"[Storage] Pruning old history record from: {date_str}")
            except (ValueError, TypeError) as e:
                # If date is invalid, let's keep it to be safe or ignore if corrupted.
                # In this case we'll discard corrupt records to avoid crashes.
                print(f"[Storage] Discarding corrupt history entry: {record} ({e})")
                
        return pruned
