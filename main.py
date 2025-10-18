#!/usr/bin/env python3
"""
RAGnosis Bot - AI Medical Assistant
Fully functional Telegram bot without SQLite
"""

import os
import asyncio
import random
from datetime import datetime
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    print("💡 Add it to Railway Secrets")
    exit(1)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found!")
    print("💡 Add it to Railway Secrets")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Conversation states
SYMPTOMS, AGE, GENDER, DURATION, SEVERITY = range(5)

# Symptom categories
SYMPTOM_CATEGORIES = [
    ["🤒 Fever", "😴 Fatigue", "🤧 Cough", "🤢 Nausea"],
    ["🤕 Headache", "😵 Dizziness", "🔴 Pain", "💩 Diarrhea"],
    ["💨 Shortness", "👃 Runny Nose", "🔥 Burning", "🩸 Bleeding"],
    ["✅ Done Selecting", "🔄 Start Over"]
]

# Health tips
HEALTH_TIPS = [
    "💧 Drink 8 glasses of water daily for proper hydration",
    "😴 Get 7-9 hours of sleep for optimal health",
    "🏃 Exercise 30 minutes daily to boost immunity", 
    "🥗 Eat fruits and vegetables for essential nutrients",
    "🧘 Practice deep breathing to reduce stress",
    "☀️ Get 15 minutes of sunlight for Vitamin D",
    "📱 Take screen breaks to protect your eyes",
    "🤝 Stay socially connected for mental health"
]

class MedicalBot:
    def __init__(self):
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        self.user_sessions: Dict[int, Dict] = {}
        self.user_stats: Dict[int, Dict] = {}  # Simple in-memory storage
        print("✅ RAGnosis Bot initialized successfully!")

    def log_usage(self, user_id: int, username: str, first_name: str):
        """Simple usage logging without database"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'username': username,
                'first_name': first_name,
                'usage_count': 0,
                'last_used': datetime.now().isoformat()
            }
        
        self.user_stats[user_id]['usage_count'] += 1
        self.user_stats[user_id]['last_used'] = datetime.now().isoformat()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.log_usage(user.id, user.username, user.first_name)
        
        welcome_text = f"""
👋 Hello *{user.first_name}*! 

I'm *RAGnosis* - Your AI Medical Assistant 🤖

I can help you:
• 🔍 Analyze symptoms 
• 💡 Provide health information
• 🎯 Give personalized recommendations
• 📊 Track your health concerns

*Choose an option below to get started!*
        """
        
        keyboard = [
            [KeyboardButton("🔍 Symptom Analysis"), KeyboardButton("💊 Drug Info")],
            [KeyboardButton("🎲 Health Tip"), KeyboardButton("📊 My Stats")],
            [KeyboardButton("🚨 Emergency Help"), KeyboardButton("ℹ️ About")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
*RAGnosis Bot Help* 🤖

*Available Commands:*
/start - Start the bot
/help - Show this help message
/analyze - Start symptom analysis
/stats - Show your usage statistics

*Quick Actions:*
🔍 Symptom Analysis - Get AI-powered symptom analysis
💊 Drug Info - Get medication information  
🎲 Health Tip - Random health tip
📊 My Stats - Your usage statistics
🚨 Emergency Help - Emergency resources
ℹ️ About - About this bot

*How to use:*
1. Click '🔍 Symptom Analysis'
2. Select your symptoms
3. Answer a few questions
4. Get AI-powered insights!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start symptom analysis"""
        return await self.start_symptom_analysis(update, context)

    async def start_symptom_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start symptom analysis conversation"""
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {
            'symptoms': [],
            'start_time': datetime.now()
        }
        
        instruction = """
*Symptom Analysis* 🔍

Please select your symptoms from the buttons below.
You can select multiple symptoms.

When finished, click *✅ Done Selecting*
        """
        
        reply_markup = ReplyKeyboardMarkup(SYMPTOM_CATEGORIES, resize_keyboard=True)
        await update.message.reply_text(instruction, reply_markup=reply_markup, parse_mode='Markdown')
        
        return SYMPTOMS

    async def handle_symptoms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symptom selection"""
        user_id = update.effective_user.id
        text = update.message.text
        session = self.user_sessions.get(user_id, {})
        
        if text == "✅ Done Selecting":
            if not session.get('symptoms'):
                await update.message.reply_text("❌ Please select at least one symptom!")
                return SYMPTOMS
            
            # Move to age selection
            age_keyboard = [
                ["👶 0-18 years", "👨 19-40 years"],
                ["👨‍🦳 41-65 years", "👴 65+ years"],
                ["🚫 Prefer not to say"]
            ]
            reply_markup = ReplyKeyboardMarkup(age_keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "👤 *Age Group*\n\nSelect your age group for better analysis:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return AGE
            
        elif text == "🔄 Start Over":
            session['symptoms'] = []
            reply_markup = ReplyKeyboardMarkup(SYMPTOM_CATEGORIES, resize_keyboard=True)
            await update.message.reply_text("🔄 Starting over... Select your symptoms:", reply_markup=reply_markup)
            return SYMPTOMS
            
        else:
            # Add symptom to selection
            if 'symptoms' not in session:
                session['symptoms'] = []
            
            if text in session['symptoms']:
                session['symptoms'].remove(text)
                action = "removed"
            else:
                session['symptoms'].append(text)
                action = "added"
            
            selection_text = ", ".join(session['symptoms']) if session['symptoms'] else "None selected"
            await update.message.reply_text(
                f"✅ {action.capitalize()} *{text}*\n\n"
                f"📋 Current selection: {selection_text}\n\n"
                f"Continue selecting or click *✅ Done Selecting* when ready.",
                parse_mode='Markdown'
            )
            return SYMPTOMS

    async def handle_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle age selection"""
        user_id = update.effective_user.id
        self.user_sessions[user_id]['age'] = update.message.text
        
        gender_keyboard = [["👨 Male", "👩 Female"], ["⚧ Other", "🚫 Prefer not to say"]]
        reply_markup = ReplyKeyboardMarkup(gender_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "👤 *Biological Sex*\n\nThis helps provide more accurate recommendations:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return GENDER

    async def handle_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle gender selection"""
        user_id = update.effective_user.id
        self.user_sessions[user_id]['gender'] = update.message.text
        
        duration_keyboard = [
            ["⏱️ Less than 24 hours", "🕐 1-3 days"],
            ["🕑 3-7 days", "🕒 1-4 weeks"],
            ["🕓 Over 1 month", "❓ Not sure"]
        ]
        reply_markup = ReplyKeyboardMarkup(duration_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "⏰ *Symptom Duration*\n\nHow long have you had these symptoms?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return DURATION

    async def handle_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle duration selection"""
        user_id = update.effective_user.id
        self.user_sessions[user_id]['duration'] = update.message.text
        
        severity_keyboard = [
            ["😊 Mild - Noticeable but not disruptive", "😐 Moderate - Affects daily activities"],
            ["😫 Severe - Significantly disruptive", "🚨 Critical - Requires immediate attention"]
        ]
        reply_markup = ReplyKeyboardMarkup(severity_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📊 *Symptom Severity*\n\nHow severe are your symptoms?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return SEVERITY

    async def handle_severity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle severity selection and provide AI analysis"""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        session['severity'] = update.message.text
        
        await update.message.reply_text("🔄 Analyzing your symptoms with AI...")
        await update.message.chat.send_action(action="typing")
        
        try:
            # Prepare context for AI
            symptoms_text = ", ".join(session['symptoms'])
            age = session.get('age', 'Not specified')
            gender = session.get('gender', 'Not specified')
            duration = session.get('duration', 'Not specified')
            severity = session.get('severity', 'Not specified')
            
            prompt = f"""
            As a medical AI assistant, analyze these symptoms:

            PATIENT INFORMATION:
            - Symptoms: {symptoms_text}
            - Age Group: {age}
            - Biological Sex: {gender}
            - Duration: {duration} 
            - Severity: {severity}

            Provide a helpful medical analysis with:

            🎯 QUICK ASSESSMENT
            [Brief overview of potential concerns]

            ⚠️ POSSIBLE CONDITIONS
            [2-3 most likely possibilities]

            💡 RECOMMENDATIONS
            [Immediate actions and self-care tips]

            🏥 WHEN TO SEE A DOCTOR
            [Clear guidance on seeking medical help]

            Keep it concise, empathetic, and informative. Use simple language.
            """
            
            response = self.gemini_model.generate_content(prompt)
            analysis = response.text
            
            # Send analysis
            await update.message.reply_text(
                f"🔬 *AI Medical Analysis Complete*\n\n{analysis}\n\n"
                f"💡 *Remember:* This is AI-assisted guidance, not a medical diagnosis. "
                f"Always consult healthcare professionals for serious concerns.",
                parse_mode='Markdown'
            )
            
            # Show follow-up options
            followup_keyboard = [
                [KeyboardButton("🔄 New Analysis"), KeyboardButton("💊 Drug Info")],
                [KeyboardButton("🎲 Health Tip"), KeyboardButton("🏠 Main Menu")]
            ]
            reply_markup = ReplyKeyboardMarkup(followup_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(
                "❌ Sorry, I encountered an error analyzing your symptoms. "
                "Please try again or contact a healthcare provider directly."
            )
            print(f"AI Analysis error: {e}")
        
        return ConversationHandler.END

    async def handle_health_tip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send random health tip"""
        tip = random.choice(HEALTH_TIPS)
        await update.message.reply_text(f"💡 *Health Tip:*\n\n{tip}", parse_mode='Markdown')

    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user = update.effective_user
        user_id = user.id
        
        if user_id in self.user_stats:
            stats = self.user_stats[user_id]
            stats_text = f"""
📊 *Your RAGnosis Stats*

👤 User: {user.first_name}
📈 Sessions: {stats['usage_count']}
🕒 Last Used: {stats['last_used'][:16]}

Thank you for using RAGnosis! 🎉
            """
        else:
            stats_text = "📊 No usage data found. Start using the bot to see your stats!"
            
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def handle_emergency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Emergency help information"""
        emergency_text = """
🚨 *EMERGENCY HELP*

If you're experiencing a medical emergency:
• 🏥 Call emergency services immediately
• 🚑 Go to the nearest hospital
• 📞 Contact your local emergency number

*Emergency Signs:*
• Difficulty breathing
• Chest pain or pressure
• Severe bleeding
• Sudden weakness or numbness
• Severe allergic reaction
• Thoughts of self-harm

*Remember:* This bot is for informational purposes only and cannot replace emergency medical care.
        """
        await update.message.reply_text(emergency_text, parse_mode='Markdown')

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About the bot"""
        about_text = """
ℹ️ *About RAGnosis Bot*

🤖 *RAGnosis - AI Medical Assistant*

*Features:*
• 🔍 AI-powered symptom analysis
• 💊 Medication information
• 💡 Health tips and education
• 📊 Usage analytics
• 🚨 Emergency guidance

*Technology:*
• Powered by Google Gemini AI
• Built with Python Telegram Bot
• Secure and private

*Disclaimer:*
This bot provides AI-assisted health information and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.

*Developer:* Your RAGnosis Team 🩺
        """
        await update.message.reply_text(about_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all other messages"""
        text = update.message.text
        
        if text == "🔍 Symptom Analysis":
            await self.start_symptom_analysis(update, context)
        elif text == "🎲 Health Tip":
            await self.handle_health_tip(update, context)
        elif text == "📊 My Stats":
            await self.handle_stats(update, context)
        elif text == "🚨 Emergency Help":
            await self.handle_emergency(update, context)
        elif text == "ℹ️ About":
            await self.handle_about(update, context)
        elif text == "💊 Drug Info":
            await update.message.reply_text(
                "💊 *Drug Information*\n\n"
                "For medication information, please consult:\n\n"
                "• Your healthcare provider\n"
                "• Licensed pharmacist\n"
                "• Reputable medical sources\n\n"
                "*Safety First:* Always follow prescribed dosages and consult professionals before taking any medication.",
                parse_mode='Markdown'
            )
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
        else:
            await update.message.reply_text(
                "🤖 I'm your RAGnosis AI assistant! "
                "Use the menu buttons or type /help to see what I can do."
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text(
            "Conversation cancelled. Type /start to begin again.",
            reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
        )
        return ConversationHandler.END

def main():
    """Start the bot"""
    print("🚀 Starting RAGnosis Medical Bot...")
    
    # Create bot instance
    medical_bot = MedicalBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add conversation handler for symptom analysis
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('analyze', medical_bot.start_symptom_analysis),
            MessageHandler(filters.Regex('^🔍 Symptom Analysis$'), medical_bot.start_symptom_analysis)
        ],
        states={
            SYMPTOMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_symptoms)
            ],
            AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_age)
            ],
            GENDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_gender)
            ],
            DURATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_duration)
            ],
            SEVERITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_severity)
            ]
        },
        fallbacks=[CommandHandler('cancel', medical_bot.cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", medical_bot.start_command))
    application.add_handler(CommandHandler("help", medical_bot.help_command))
    application.add_handler(CommandHandler("stats", medical_bot.handle_stats))
    application.add_handler(conv_handler)
    
    # Add message handler for all other messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, medical_bot.handle_message))
    
    # Start the bot
    print("✅ Bot setup completed!")
    print("🤖 RAGnosis Bot is now running...")
    print("📱 Send /start to your bot on Telegram to test it!")
    
    application.run_polling()

if __name__ == '__main__':
    main()
