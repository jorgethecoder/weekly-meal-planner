import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List
import config
from recipe_client import Recipe

class EmailManager:
    """Generates structured HTML emails and sends them via Gmail SMTP."""
    
    def __init__(self):
        self.username = config.GMAIL_USER
        self.password = config.GMAIL_APP_PASSWORD
        self.recipient = config.RECIPIENT_EMAIL

    def send_weekly_email(self, plan: Dict[str, Dict[str, Recipe]], grocery_list: Dict[str, List[str]]) -> None:
        """Constructs and sends the weekly meal planner email."""
        # 1. Validate configuration before sending
        config.validate_config()
        
        # 2. Build HTML body
        html_content = self.generate_html_content(plan, grocery_list)
        
        # 3. Create MIME Message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🌿 Your Weekly Meal Plan & Grocery List"
        msg["From"] = self.username
        msg["To"] = self.recipient
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))
        
        # 4. Connect to SMTP server and send
        print(f"[Email] Connecting to Gmail SMTP server for {self.recipient}...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.starttls()  # Upgrade connection to secure TLS
                server.login(self.username, self.password)
                server.send_message(msg)
                print("[Email] Weekly meal plan and grocery list successfully sent!")
        except Exception as e:
            print(f"[Email] Error sending email: {e}")
            raise

    def generate_html_content(self, plan: Dict[str, Dict[str, Recipe]], grocery_list: Dict[str, List[str]]) -> str:
        """Generates the modern, styled HTML body for the email."""
        
        # Generate Meal Plan HTML section
        meal_plan_html = ""
        for day, meals in plan.items():
            meal_plan_html += f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <h3 style="margin-top: 0; color: #0d9488; font-size: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; font-weight: 700;">{day}</h3>
                
                <!-- Breakfast -->
                <div style="margin-bottom: 12px;">
                    <span style="background-color: #f0fdf4; color: #166534; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 12px; display: inline-block; margin-bottom: 4px;">🍳 Breakfast</span>
                    <div style="font-size: 15px; font-weight: 600; color: #1e293b;">
                        {self._format_recipe_title(meals['breakfast'])}
                        <span style="font-size: 13px; font-weight: 400; color: #64748b; margin-left: 6px;">(~{int(meals['breakfast'].calories)} kcal total)</span>
                    </div>
                </div>
                
                <!-- Lunch -->
                <div style="margin-bottom: 12px;">
                    <span style="background-color: #eff6ff; color: #1e40af; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 12px; display: inline-block; margin-bottom: 4px;">🥗 Lunch</span>
                    <div style="font-size: 15px; font-weight: 600; color: #1e293b;">
                        {self._format_recipe_title(meals['lunch'])}
                        <span style="font-size: 13px; font-weight: 400; color: #64748b; margin-left: 6px;">(~{int(meals['lunch'].calories)} kcal total)</span>
                    </div>
                </div>
                
                <!-- Dinner -->
                <div style="margin-bottom: 0;">
                    <span style="background-color: #fff7ed; color: #9a3412; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 12px; display: inline-block; margin-bottom: 4px;">🍽️ Dinner</span>
                    <div style="font-size: 15px; font-weight: 600; color: #1e293b;">
                        {self._format_recipe_title(meals['dinner'])}
                        <span style="font-size: 13px; font-weight: 400; color: #64748b; margin-left: 6px;">(~{int(meals['dinner'].calories)} kcal total)</span>
                    </div>
                </div>
            </div>
            """

        # Generate Grocery List HTML section
        grocery_html = ""
        category_emojis = {
            "vegetables": "🥬 Vegetables & Fruits",
            "proteins": "🥩 Proteins (Meat & Fish)",
            "pantry staples": "🧂 Pantry Staples & Grains",
            "dairy alternatives": "🥛 Dairy & Lactose Alternatives",
            "others": "📦 Other Ingredients"
        }

        for category, items in grocery_list.items():
            if not items:
                continue
                
            category_title = category_emojis.get(category, category.title())
            
            items_list = ""
            for item in items:
                items_list += f"""
                <li style="padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: #334155; display: flex; align-items: center;">
                    <span style="color: #cbd5e1; margin-right: 10px; font-size: 16px; font-family: monospace;">☐</span> {item}
                </li>
                """

            grocery_html += f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <h4 style="margin-top: 0; color: #334155; font-size: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">{category_title}</h4>
                <ul style="list-style-type: none; padding-left: 0; margin: 0;">
                    {items_list}
                </ul>
            </div>
            """

        # Full responsive email skeleton
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Meal Plan & Grocery List</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 20px 10px;">
                <tr>
                    <td align="center">
                        <table width="100%" max-width="650" style="max-width: 650px; background-color: transparent; border-collapse: collapse;">
                            <!-- Header Brand Banner -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); border-radius: 16px 16px 0 0; padding: 35px 20px; text-align: center; color: #ffffff;">
                                    <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">Weekly Harvest</h1>
                                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ccfbf1; font-weight: 400;">Your Automated Meal Planner & Shopping Companion</p>
                                </td>
                            </tr>
                            
                            <!-- Portion & Calorie Alert Banner -->
                            <tr>
                                <td style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; padding: 24px 24px 10px 24px;">
                                    <div style="background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 12px; padding: 16px; color: #115e59;">
                                        <h3 style="margin-top: 0; margin-bottom: 6px; font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">⚖️ Daily Calorie & Serving Partition Instructions</h3>
                                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                                            This meal plan is tailored for a combined daily target of <strong>4,500 kcal</strong>:
                                        </p>
                                        <ul style="margin: 6px 0; padding-left: 20px; font-size: 14px; line-height: 1.5;">
                                            <li><strong>Person A (2,500 kcal):</strong> Eat exactly <strong>5/9 (55.6%)</strong> of the prepared dish.</li>
                                            <li><strong>Person B (2,000 kcal):</strong> Eat exactly <strong>4/9 (44.4%)</strong> of the prepared dish.</li>
                                        </ul>
                                        <p style="margin: 0; font-size: 12px; color: #0d9488; font-style: italic;">
                                            *All recipes and their ingredient lists below have been scaled dynamically for these combined portions.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Section Title: Meal Plan -->
                            <tr>
                                <td style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; padding: 20px 24px 10px 24px;">
                                    <h2 style="margin: 0; font-size: 20px; color: #1e293b; font-weight: 800;">📅 Weekly Meal Plan</h2>
                                </td>
                            </tr>
                            
                            <!-- Meal Cards -->
                            <tr>
                                <td style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; padding: 0 24px 10px 24px;">
                                    {meal_plan_html}
                                </td>
                            </tr>
                            
                            <!-- Section Title: Groceries -->
                            <tr>
                                <td style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; padding: 20px 24px 10px 24px;">
                                    <h2 style="margin: 0; font-size: 20px; color: #1e293b; font-weight: 800;">🛒 Consolidated Grocery List</h2>
                                </td>
                            </tr>
                            
                            <!-- Grocery Lists -->
                            <tr>
                                <td style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-radius: 0 0 16px 16px; padding: 0 24px 30px 24px; border-bottom: 1px solid #e2e8f0;">
                                    {grocery_html}
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 25px 20px; text-align: center; color: #94a3b8; font-size: 12px; line-height: 1.5;">
                                    <p style="margin: 0;">This email was automatically generated and sent via GitHub Actions.</p>
                                    <p style="margin: 5px 0 0 0;">&copy; 2026 Weekly Harvest. Built for Python Automated Systems Course.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html_template

    def _format_recipe_title(self, recipe: Recipe) -> str:
        """Helper to format recipe title as a link if a source URL is available."""
        if recipe.source_url:
            return f'<a href="{recipe.source_url}" target="_blank" style="color: #0d9488; text-decoration: none; border-bottom: 1px dashed #0d9488;">{recipe.title}</a>'
        return recipe.title
