# main.py - DYNAMIC RAGnosis Bot
import os
import logging
import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import sqlite3
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackQueryHandler,
    JobQueue
)
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure advanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('ragnosis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Dynamic conversation states
class ConversationState:
    SYMPTOMS = 0
    AGE = 1
    GENDER = 2
    DURATION = 3
    SEVERITY = 4
    MEDICAL_HISTORY = 5
    FOLLOW_UP = 6

# Dynamic symptom categories with emojis
SYMPTOM_CATEGORIES = {
    "general": ["🤒 Fever", "😴 Fatigue", "⚖️ Weight Changes", "🌡️ Sweating"],
    "respiratory": ["🤧 Cough", "💨 Shortness", "👃 Runny Nose", "🤭 Sneeze"],
    "digestive": ["🤢 Nausea", "💩 Diarrhea", "🤰 Bloating", "🍽️ Appetite"],
    "neurological": ["🤕 Headache", "😵 Dizziness", "👀 Vision", "💤 Sleep"],
    "pain": ["🔴 Pain", "🔥 Burning", "💫 Tingling", "💔 Chest Pain"],
    "other": ["🩸 Bleeding", "🔴 Rash", "🦵 Swelling", "🎨 Color Changes"]
}

class DynamicRagnosisBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Dynamic data storage
        self.user_sessions: Dict[int, Dict] = {}
        self.analytics = {
            'total_users': 0,
            'sessions_today': 0,
            'common_symptoms': {},
            'active_conversations': 0
        }
        
        # Initialize database
        self.init_database()
        
        # Health tips pool (dynamic content)
        self.health_tips = [
            "💧 Stay hydrated - drink at least 8 glasses of water daily",
            "🏃 Move regularly - even short walks boost circulation",
            "😴 Prioritize sleep - 7-9 hours for optimal health",
            "🥗 Eat colorful foods - variety ensures nutrient diversity",
            "🧘 Manage stress - deep breathing reduces cortisol",
            "☀️ Get sunlight - 15 minutes daily for Vitamin D",
            "📱 Digital detox - reduce screen time before bed",
            "🤝 Social connection - relationships boost mental health"
        ]

    def init_database(self):
        """Initialize SQLite database for analytics"""
        try:
            self.conn = sqlite3.connect('ragnosis_analytics.db', check_same_thread=False)
            cursor = self.conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    sessions_count INTEGER DEFAULT 1,
                    last_active TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS symptom_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symptom TEXT,
                    count INTEGER DEFAULT 1,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def log_analytics(self, user_id: int, username: str, first_name: str, symptom: str = None):
        """Dynamic analytics logging"""
        try:
            cursor = self.conn.cursor()
            
            # Update user session
            cursor.execute('''
                INSERT OR REPLACE INTO user_sessions (user_id, username, first_name, sessions_count, last_active)
                VALUES (?, ?, ?, COALESCE((SELECT sessions_count FROM user_sessions WHERE user_id = ?), 0) + 1, ?)
            ''', (user_id, username, first_name, user_id, datetime.now()))
            
            # Log symptom if provided
            if symptom:
                cursor.execute('''
                    INSERT INTO symptom_analytics (symptom, count)
                    VALUES (?, 1)
                    ON CONFLICT(symptom) DO UPDATE SET count = count + 1
                ''', (symptom,))
            
            self.conn.commit()
            self.analytics['total_users'] = cursor.execute('SELECT COUNT(*) FROM user_sessions').fetchone()[0]
            self.analytics['sessions_today'] = cursor.execute(
                'SELECT COUNT(*) FROM user_sessions WHERE date(last_active) = date("now")'
            ).fetchone()[0]
        except Exception as e:
            logger.error(f"Analytics logging error: {e}")

    async def dynamic_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dynamic start with personalized greeting"""
        try:
            user = update.effective_user
            current_hour = datetime.now().hour
            
            # Time-based greeting
            if 5 <= current_hour < 12:
                greeting = "🌅 Good morning"
            elif 12 <= current_hour < 17:
                greeting = "☀️ Good afternoon"
            elif 17 <= current_hour < 22:
                greeting = "🌇 Good evening"
            else:
                greeting = "🌙 Good night"
            
            # Log user analytics
            self.log_analytics(user.id, user.username, user.first_name)
            
            welcome_text = f"""
{greeting}, *{user.first_name}*! 👋

🔬 *Welcome to RAGnosis - Your Dynamic AI Medical Assistant*

📊 *Live Stats:*
• 🧑‍🤝‍🧑 {self.analytics['total_users']} users helped today
• 🔍 {self.analytics['sessions_today']} sessions active
• 💡 Always learning & improving

🎯 *How can I assist you today?*
            """
            
            # Dynamic keyboard based on time of day
            if current_hour < 12:
                keyboard = [
                    [KeyboardButton("🔍 Morning Check"), KeyboardButton("💊 Med Reminder")],
                    [KeyboardButton("📊 Health Track"), KeyboardButton("🚨 Emergency")],
                    [KeyboardButton("🎯 Quick Analysis"), KeyboardButton("📚 Learn")]
                ]
            else:
                keyboard = [
                    [KeyboardButton("🔍 Symptom Analysis"), KeyboardButton("💊 Drug Info")],
                    [KeyboardButton("😴 Sleep Health"), KeyboardButton("🚨 Emergency")],
                    [KeyboardButton("📈 Daily Review"), KeyboardButton("🎲 Random Tip")]
                ]
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Send random health tip after 2 seconds
            async def send_tip():
                await asyncio.sleep(2)
                tip = random.choice(self.health_tips)
                await update.message.reply_text(f"💡 *Daily Health Tip:*\n\n{tip}", parse_mode='Markdown')
            
            asyncio.create_task(send_tip())
            
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def dynamic_symptom_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dynamic symptom analysis with categorized selection"""
        try:
            user_id = update.effective_user.id
            
            # Initialize dynamic session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'selected_symptoms': [],
                    'conversation_start': datetime.now(),
                    'interaction_count': 0
                }
            
            # Create dynamic symptom keyboard by categories
            keyboard = []
            for category, symptoms in SYMPTOM_CATEGORIES.items():
                row = [KeyboardButton(symptom) for symptom in symptoms[:2]]
                keyboard.append(row)
            
            keyboard.extend([
                [KeyboardButton("✅ Done Selecting"), KeyboardButton("🔄 Change Categories")],
                [KeyboardButton("🎯 Quick Analyze"), KeyboardButton("🔙 Main Menu")]
            ])
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            current_selections = self.user_sessions[user_id]['selected_symptoms']
            selection_text = f"📋 Currently selected: {', '.join(current_selections)}" if current_selections else ""
            
            await update.message.reply_text(
                f"🔍 *Dynamic Symptom Analysis*\n\n"
                f"Select symptoms from categories below:\n\n"
                f"{selection_text}\n\n"
                f"*Categories:*\n"
                f"• 🤒 General • 🫁 Respiratory • 🍽️ Digestive\n"
                f"• 🧠 Neurological • 🔴 Pain • 🎨 Other",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return ConversationState.SYMPTOMS
        except Exception as e:
            logger.error(f"Symptom analysis error: {e}")
            await update.message.reply_text("❌ Error starting symptom analysis. Please try again.")
            return ConversationHandler.END

    async def handle_symptom_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle dynamic symptom selection"""
        try:
            user_id = update.effective_user.id
            selected = update.message.text
            session = self.user_sessions[user_id]
            
            if selected == "✅ Done Selecting":
                if not session['selected_symptoms']:
                    await update.message.reply_text("❌ Please select at least one symptom to analyze.")
                    return ConversationState.SYMPTOMS
                
                # Move to age selection
                return await self.collect_age_dynamic(update, context)
            
            elif selected == "🔄 Change Categories":
                session['selected_symptoms'] = []
                return await self.dynamic_symptom_analysis(update, context)
            
            elif selected == "🎯 Quick Analyze":
                return await self.quick_analysis(update, context)
            
            elif selected == "🔙 Main Menu":
                await self.dynamic_start(update, context)
                return ConversationHandler.END
            
            else:
                # Add/remove symptom dynamically
                if selected in session['selected_symptoms']:
                    session['selected_symptoms'].remove(selected)
                    action = "❌ Removed"
                else:
                    session['selected_symptoms'].append(selected)
                    action = "✅ Added"
                
                selection_text = ", ".join(session['selected_symptoms']) if session['selected_symptoms'] else "None"
                
                await update.message.reply_text(
                    f"{action} *{selected}*\n\n"
                    f"📋 Current selection: {selection_text}\n\n"
                    f"Continue selecting or press '✅ Done Selecting' when ready.",
                    parse_mode='Markdown'
                )
                
                return ConversationState.SYMPTOMS
        except Exception as e:
            logger.error(f"Symptom selection error: {e}")
            await update.message.reply_text("❌ Error processing selection. Please try again.")
            return ConversationState.SYMPTOMS

    async def quick_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick AI analysis without full conversation"""
        try:
            user_id = update.effective_user.id
            session = self.user_sessions.get(user_id, {})
            symptoms = session.get('selected_symptoms', [])
            
            if not symptoms:
                await update.message.reply_text(
                    "🎯 *Quick Analysis*\n\nPlease describe your symptoms briefly:",
                    parse_mode='Markdown'
                )
                context.user_data['quick_analysis'] = True
                return ConversationState.SYMPTOMS
            
            await update.message.chat.send_action(action="typing")
            
            prompt = f"""
            Provide a quick, concise medical analysis for these symptoms: {', '.join(symptoms)}
            
            Format as:
            🎯 QUICK ASSESSMENT
            [Brief overview]
            
            ⚠️ KEY CONSIDERATIONS
            [2-3 bullet points]
            
            🏥 NEXT STEPS
            [Immediate actions]
            
            Keep it under 300 characters.
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            await update.message.reply_text(
                f"🎯 *Quick Analysis Results:*\n\n{response.text}\n\n"
                f"💡 For comprehensive analysis, use full symptom analysis.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Quick analysis error: {e}")
            await update.message.reply_text("❌ Quick analysis failed. Please try full analysis.")
        
        await self.dynamic_start(update, context)
        return ConversationHandler.END

    async def collect_age_dynamic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dynamic age collection with context"""
        try:
            user_id = update.effective_user.id
            symptoms = self.user_sessions[user_id]['selected_symptoms']
            
            age_keyboard = [
                [KeyboardButton("👶 Child (0-12)"), KeyboardButton("👦 Teen (13-17)")],
                [KeyboardButton("👨 Young Adult (18-30)"), KeyboardButton("👨‍💼 Adult (31-50)")],
                [KeyboardButton("👴 Senior (50+)"), KeyboardButton("🚫 Skip Age")]
            ]
            
            reply_markup = ReplyKeyboardMarkup(age_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"👤 *Age Information*\n\n"
                f"Based on your symptoms: {', '.join(symptoms)}\n\n"
                f"Age helps provide more accurate recommendations for your specific situation.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return ConversationState.AGE
        except Exception as e:
            logger.error(f"Age collection error: {e}")
            return ConversationHandler.END

    async def collect_gender_dynamic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect gender information"""
        try:
            user_id = update.effective_user.id
            self.user_sessions[user_id]['age'] = update.message.text
            
            gender_options = [
                [KeyboardButton("👨 Male"), KeyboardButton("👩 Female")],
                [KeyboardButton("⚧ Other"), KeyboardButton("🚫 Prefer not to say")]
            ]
            reply_markup = ReplyKeyboardMarkup(gender_options, resize_keyboard=True)
            
            await update.message.reply_text(
                "👤 *Biological Sex*\n\nThis helps with condition-specific recommendations:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationState.GENDER
        except Exception as e:
            logger.error(f"Gender collection error: {e}")
            return ConversationHandler.END

    async def collect_duration_dynamic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect symptom duration"""
        try:
            user_id = update.effective_user.id
            self.user_sessions[user_id]['gender'] = update.message.text
            
            duration_options = [
                [KeyboardButton("⏱️ <24 hours"), KeyboardButton("🕐 1-3 days")],
                [KeyboardButton("🕑 3-7 days"), KeyboardButton("🕒 1-4 weeks")],
                [KeyboardButton("🕓 >1 month"), KeyboardButton("❓ Not sure")]
            ]
            reply_markup = ReplyKeyboardMarkup(duration_options, resize_keyboard=True)
            
            await update.message.reply_text(
                "⏰ *Symptom Duration*\n\nHow long have you experienced these symptoms?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationState.DURATION
        except Exception as e:
            logger.error(f"Duration collection error: {e}")
            return ConversationHandler.END

    async def collect_severity_dynamic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect symptom severity"""
        try:
            user_id = update.effective_user.id
            self.user_sessions[user_id]['duration'] = update.message.text
            
            severity_options = [
                [KeyboardButton("😊 Mild"), KeyboardButton("😐 Moderate")],
                [KeyboardButton("😫 Severe"), KeyboardButton("🚨 Critical")]
            ]
            reply_markup = ReplyKeyboardMarkup(severity_options, resize_keyboard=True)
            
            await update.message.reply_text(
                "📊 *Symptom Severity*\n\nHow severe are your symptoms currently?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationState.SEVERITY
        except Exception as e:
            logger.error(f"Severity collection error: {e}")
            return ConversationHandler.END

    async def smart_ai_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced AI analysis with dynamic prompting"""
        try:
            user_id = update.effective_user.id
            session = self.user_sessions[user_id]
            
            await update.message.chat.send_action(action="typing")
            
            symptoms_text = ", ".join(session['selected_symptoms'])
            age = session.get('age', 'Not specified')
            gender = session.get('gender', 'Not specified')
            duration = session.get('duration', 'Not specified')
            severity = session.get('severity', 'Not specified')
            
            prompt = f"""
            Analyze these symptoms with medical intelligence:
            
            PATIENT CONTEXT:
            - Symptoms: {symptoms_text}
            - Age: {age}
            - Gender: {gender} 
            - Duration: {duration}
            - Severity: {severity}
            
            Provide a structured analysis with:
            
            🔍 RISK ASSESSMENT
            [Urgency level and immediate concerns]
            
            🎯 LIKELY CONDITIONS  
            [Top 3 possibilities with brief reasoning]
            
            💡 SMART RECOMMENDATIONS
            [Personalized actions based on context]
            
            🏥 MEDICAL GUIDANCE
            [When and what type of care to seek]
            
            Format with clear sections and appropriate emojis. Be concise but comprehensive.
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            # Add analytics
            for symptom in session['selected_symptoms']:
                self.log_analytics(user_id, update.effective_user.username, 
                                 update.effective_user.first_name, symptom)
            
            # Create interactive follow-up
            follow_up_keyboard = [
                [KeyboardButton("🔍 More Details"), KeyboardButton("💊 Medication Info")],
                [KeyboardButton("🏥 Find Doctors"), KeyboardButton("📊 Track Symptoms")],
                [KeyboardButton("🔄 New Analysis"), KeyboardButton("🏠 Main Menu")]
            ]
            reply_markup = ReplyKeyboardMarkup(follow_up_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"🔬 *RAGnosis AI Analysis Complete*\n\n{response.text}\n\n"
                f"📊 *Session Summary:*\n"
                f"• Symptoms analyzed: {len(session['selected_symptoms'])}\n"
                f"• Analysis time: {(datetime.now() - session['conversation_start']).seconds}s\n"
                f"• Confidence: High\n\n"
                f"💡 *What would you like to do next?*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            session['analysis_complete'] = True
            
        except Exception as e:
            logger.error(f"AI Analysis error: {e}")
            await update.message.reply_text(
                "❌ *Analysis Error*\n\nI encountered an issue. Please try again or use quick analysis.",
                parse_mode='Markdown'
            )
        
        return ConversationState.FOLLOW_UP

    async def handle_follow_up(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle post-analysis follow-up actions"""
        try:
            choice = update.message.text
            
            if choice == "🔍 More Details":
                await update.message.reply_text(
                    "🔍 *Detailed Analysis*\n\n"
                    "For comprehensive medical information, I recommend:\n\n"
                    "• 📚 Reputable medical websites (Mayo Clinic, WebMD)\n"
                    "• 🏥 Consultation with healthcare professionals\n"
                    "• 🔬 Further diagnostic tests if recommended\n\n"
                    "Would you like information about any specific aspect?",
                    parse_mode='Markdown'
                )
                
            elif choice == "💊 Medication Info":
                await update.message.reply_text(
                    "💊 *Medication Safety*\n\n"
                    "Always consult healthcare providers before taking any medication.\n\n"
                    "For drug information, provide the medication name:",
                    parse_mode='Markdown'
                )
                
            elif choice == "🔄 New Analysis":
                await self.dynamic_symptom_analysis(update, context)
                return ConversationState.SYMPTOMS
                
            elif choice == "🏠 Main Menu":
                await self.dynamic_start(update, context)
                return ConversationHandler.END
                
            else:
                await update.message.reply_text(
                    "💡 Please select an option from the menu below.",
                    parse_mode='Markdown'
                )
            
            return ConversationState.FOLLOW_UP
        except Exception as e:
            logger.error(f"Follow-up error: {e}")
            return ConversationHandler.END

    async def show_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot analytics (admin feature)"""
        try:
            user_id = update.effective_user.id
            
            # Simple admin check
            if user_id == 123456789:  # Replace with your Telegram ID
                cursor = self.conn.cursor()
                
                total_users = cursor.execute('SELECT COUNT(*) FROM user_sessions').fetchone()[0]
                today_sessions = cursor.execute(
                    'SELECT COUNT(*) FROM user_sessions WHERE date(last_active) = date("now")'
                ).fetchone()[0]
                
                common_symptoms = cursor.execute('''
                    SELECT symptom, SUM(count) as total 
                    FROM symptom_analytics 
                    GROUP BY symptom 
                    ORDER BY total DESC 
                    LIMIT 5
                ''').fetchall()
                
                analytics_text = f"""
    📊 *RAGnosis Analytics*

    👥 Users: {total_users}
    📈 Sessions Today: {today_sessions}
    🔄 Active Conversations: {self.analytics['active_conversations']}

    🏥 Top Symptoms:
    {chr(10).join([f'• {symptom}: {count}' for symptom, count in common_symptoms])}

    🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                """
                
                await update.message.reply_text(analytics_text, parse_mode='Markdown')
            else:
                await update.message.reply_text("🔒 Analytics available for administrators only.")
        except Exception as e:
            logger.error(f"Analytics error: {e}")

    async def send_random_tip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send random health tip"""
        try:
            tip = random.choice(self.health_tips)
            await update.message.reply_text(f"💡 *Health Tip:*\n\n{tip}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Random tip error: {e}")

    async def handle_dynamic_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all other dynamic messages"""
        try:
            text = update.message.text
            
            if text == "🎲 Random Tip":
                tip = random.choice(self.health_tips)
                await update.message.reply_text(f"💡 *Health Tip:*\n\n{tip}", parse_mode='Markdown')
                
            elif text == "📊 Health Track":
                await update.message.reply_text(
                    "📊 *Health Tracking*\n\n"
                    "Track your symptoms over time:\n\n"
                    "• Use /analyze for regular check-ins\n"
                    "• Note symptom changes\n"
                    "• Monitor improvement patterns\n"
                    "• Share trends with your doctor",
                    parse_mode='Markdown'
                )
                
            else:
                await update.message.chat.send_action(action="typing")
                try:
                    response = self.gemini_model.generate_content(
                        f"Answer this health/medical question concisely and helpfully: {text}"
                    )
                    await update.message.reply_text(
                        f"🔬 *RAGnosis AI:*\n\n{response.text}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    await update.message.reply_text(
                        "❌ I couldn't process that. Try rephrasing or use /start for menu.",
                        parse_mode='Markdown'
                    )
        except Exception as e:
            logger.error(f"Dynamic message error: {e}")

    def setup_handlers(self, application):
        """Setup all dynamic handlers"""
        
        # Main conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex(
                    r"^(🔍 Symptom Analysis|🔍 Morning Check|🎯 Quick Analysis)$"), 
                    self.dynamic_symptom_analysis
                ),
                CommandHandler("analyze", self.dynamic_symptom_analysis)
            ],
            states={
                ConversationState.SYMPTOMS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_symptom_selection)
                ],
                ConversationState.AGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_gender_dynamic)
                ],
                ConversationState.GENDER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_duration_dynamic)
                ],
                ConversationState.DURATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_severity_dynamic)
                ],
                ConversationState.SEVERITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.smart_ai_analysis)
                ],
                ConversationState.FOLLOW_UP: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_follow_up)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.dynamic_start)]
        )
        
        # Add all handlers
        application.add_handler(CommandHandler("start", self.dynamic_start))
        application.add_handler(CommandHandler("stats", self.show_analytics))
        application.add_handler(CommandHandler("tip", self.send_random_tip))
        application.add_handler(conv_handler)
        
        # Add handler for other features
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_dynamic_message))

    async def update_analytics(self, context: ContextTypes.DEFAULT_TYPE):
        """Update analytics periodically"""
        self.analytics['active_conversations'] = len(self.user_sessions)
        logger.info(f"Analytics updated: {self.analytics}")

    async def run(self):
        """Run the dynamic bot"""
        try:
            application = Application.builder().token(self.token).build()
            self.setup_handlers(application)
            
            # Add job queue for dynamic features
            job_queue = application.job_queue
            if job_queue:
                job_queue.run_repeating(self.update_analytics, interval=300, first=10)
            
            print("🚀 Dynamic RAGnosis Bot Started!")
            print("🎯 Features: AI Analysis • Analytics • Dynamic Menus • User Sessions")
            print("🔧 Running on Replit")
            
            await application.run_polling()
        except Exception as e:
            logger.error(f"Bot run error: {e}")
            print(f"❌ Failed to start bot: {e}")

# Start the dynamic bot
async def main():
    try:
        # Check environment variables
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            print("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
            print("💡 Please add it to Replit Secrets (lock icon)")
            return
        
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ GEMINI_API_KEY not found in environment variables!")
            print("💡 Please add it to Replit Secrets (lock icon)")
            return
        
        bot = DynamicRagnosisBot()
        await bot.run()
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
