# Weekly Harvest: Automated Meal Planner & Grocery Email System

Weekly Harvest is a production-inspired, beginner-friendly Python application that automatically plans healthy weekly meals, compiles a consolidated grocery list, and emails a beautiful HTML overview to your inbox. 

It is designed to run as a scheduled **GitHub Actions workflow** every Friday afternoon, but it can also be run locally on your computer.

---

## Key Features

- **Dynamic Calorie Scaling**: Tailored for two adults with specific daily requirements:
  - **Person A**: 2,500 kcal/day
  - **Person B**: 2,000 kcal/day (Combined target: 4,500 kcal/day)
  - Recipe ingredients are scaled dynamically so the cooked dishes meet these exact requirements.
  - Generates a **Portion Guide**: Person A eats `5/9` (~55.6%) of the cooked food; Person B eats `4/9` (~44.4%).
- **Lactose-Free & Mediterranean**: Automatically filters recipes to fit a Mediterranean-focused, dairy-free diet while avoiding Asian cuisines (per preferences).
- **Deduplication History**: Keeps a rolling 2-week history database in `meal_history.json` to prevent repeating any dishes within the same or following week.
- **Mock Mode**: Can run offline out of the box with zero setup using built-in mock recipes.

---

## File Architecture

The project has a modular design suitable for a python training course:
```
├── .github/
│   └── workflows/
│       └── meal_planner.yml   # GitHub Actions workflow schedule
├── .env.example               # Template environment file
├── .gitignore                 # Files excluded from Git tracking
├── README.md                  # Setup & usage instructions (this file)
├── requirements.txt           # Python library dependencies
├── config.py                  # Startup checks and constants configuration
├── recipe_client.py           # Spoonacular API search & Mock database client
├── filters.py                 # Secondary cuisine and lactose filters
├── planner.py                 # Daily meal selection and calorie scaling logic
├── grocery.py                 # Ingredient normalization and category compiler
├── storage.py                 # 2-week JSON history loader, saver, and pruner
├── emailer.py                 # Premium HTML email renderer and SMTP sender
└── main.py                    # Script runner and orchestrator
```

---

## Setup Instructions

### 1. Prerequisites & Installation

Make sure you have Python 3.8+ installed.

1. Clone or download this project.
2. In your terminal, navigate to the project directory:
   ```bash
   cd "Training Vibe Coding"
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### 2. Local Configuration (.env)

Duplicate the `.env.example` file and rename it to `.env`:
```bash
cp .env.example .env
```

Open the `.env` file and configure your credentials.

#### 🔑 Get a Spoonacular API Key (Free)
1. Register a free account at [Spoonacular Food API](https://spoonacular.com/food-api).
2. Go to your console/dashboard and copy your API key.
3. Paste it in `.env` as `RECIPE_API_KEY=your_api_key`.
*Note: If you leave this blank, the app will run in **Mock Mode** using 15 high-quality, pre-defined Mediterranean meals!*

#### 📧 Get a Gmail App Password
The application uses Gmail SMTP to send emails. You cannot use your regular Gmail password for scripts; you must generate an **App Password**.
1. Go to your [Google Account Settings](https://myaccount.google.com/).
2. Enable **2-Step Verification** (required by Google to generate App Passwords).
3. Search for "App Passwords" in the search bar or navigate to Security -> 2-Step Verification -> App Passwords (at the bottom).
4. Create a new App Password (name it something like "Meal Planner").
5. Copy the 16-character code generated and paste it in `.env`:
   ```env
   GMAIL_USER=your_gmail_address@gmail.com
   GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

---

### 3. Running Locally

To run the program locally:

```bash
# Run with active email delivery (requires .env configuration)
python main.py

# Run in local mode (ignores email credentials, prints to console, and saves to meal_plan.html)
python main.py --local-only
```

Once executed:
- If running normally, a beautiful styled email arrives in your inbox.
- If running locally, you can open the generated `meal_plan.html` in any web browser to see the formatted plan.
- The `meal_history.json` file is updated to record the meals selected.

---

## Production Setup (GitHub Actions Automation)

To automate this to run every Friday afternoon:

### 1. Push Code to GitHub
Push this codebase to your own private or public GitHub repository.

### 2. Set Up GitHub Secrets
Never commit your `.env` file. Instead, set the environment variables as secrets inside GitHub:
1. Go to your repository on GitHub.
2. Click **Settings** (top tabs) -> **Secrets and variables** (left sidebar) -> **Actions**.
3. Click **New repository secret** and add the following:
   - `RECIPE_API_KEY`: Your Spoonacular API Key
   - `GMAIL_USER`: Your Gmail address
   - `GMAIL_APP_PASSWORD`: Your 16-character Gmail App Password

### 3. Configure Repository Permissions
Since the GitHub Actions workflow commits the updated `meal_history.json` back to your repo to prevent repeated recipes next week, you must give the workflow write access:
1. Under repository **Settings**, go to **Actions** -> **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

### 4. Triggering Manually
You can test the GitHub action immediately:
1. Go to the **Actions** tab on your GitHub repository page.
2. Select **Automated Weekly Meal Planner** on the left.
3. Click **Run workflow** -> Select branch -> Click **Run workflow**.

---

## Under the Hood: Calorie Allocation & Portions

Our calorie model is mathematically designed to fulfill the distinct calorie requirements of two adults:

- **Person A**: 2,500 kcal/day (Portion: `5/9` or `55.6%`)
- **Person B**: 2,000 kcal/day (Portion: `4/9` or `44.4%`)
- **Daily Combined Total**: 4,500 kcal/day

### Meal Calories Distribution
We divide the daily calorie target across three main meals:
- **Breakfast**: 22% of daily budget = **1,000 kcal** combined (556 kcal for A, 444 kcal for B)
- **Lunch**: 39% of daily budget = **1,750 kcal** combined (972 kcal for A, 778 kcal for B)
- **Dinner**: 39% of daily budget = **1,750 kcal** combined (972 kcal for A, 778 kcal for B)

The program computes a scaling factor for each meal:
$$\text{Scale Factor} = \frac{\text{Meal Calorie Target}}{\text{Recipe Calories per Serving} \times \text{Recipe Servings}}$$
This factor is multiplied by the quantity of each ingredient, ensuring the total dish cooked has the exact calorie count needed. 

To eat their targeted calories, **Person A eats 55.6%** of the cooked food, and **Person B eats 44.4%**.
