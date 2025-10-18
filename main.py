#!/usr/bin/env python3
"""
🤖 MEDIX AI - Advanced Diagnostic Assistant
AI-powered medical bot with Wikipedia integration and advanced diagnostics
"""

import os
import asyncio
import random
import aiohttp
import wikipediaapi
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

# Configure AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN]):
    print("❌ Missing environment variables!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

# Wikipedia setup
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MedixAI/1.0 (https://t.me/medixai_bot)',
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Conversation states
SYMPTOMS, DETAILS, ANALYSIS = range(3)

# Advanced symptom database
SYMPTOM_DATABASE = {
    "🤒 General": ["Fever", "Fatigue", "Weight Changes", "Night Sweats", "Chills"],
    "🫁 Respiratory": ["Cough", "Shortness of Breath", "Chest Pain", "Wheezing", "Sneezing"],
    "🧠 Neurological": ["Headache", "Dizziness", "Vision Changes", "Memory Issues", "Tremors"],
    "💓 Cardiovascular": ["Chest Pain", "Palpitations", "Swelling", "High BP", "Low BP"],
    "🍽️ Digestive": ["Nausea", "Diarrhea", "Bloating", "Abdominal Pain", "Appetite Changes"],
    "🦴 Musculoskeletal": ["Joint Pain", "Back Pain", "Muscle Weakness", "Stiffness", "Swelling"],
    "😴 Mental Health": ["Anxiety", "Depression", "Insomnia", "Stress", "Mood Swings"],
    "🔬 Other": ["Skin Rash", "Frequent Urination", "Hair Loss", "Allergies", "Bleeding"]
}

# Personality traits
BOT_PERSONALITY = {
    "greetings": ["Hey there! 👋", "Hello! 🩺", "Hi! Ready to help! 🤖", "Greetings! 💫"],
    "positive_feedback": ["Great choice! 🎯", "Excellent! 🌟", "Perfect! ✅", "Awesome! 🚀"],
    "encouragement": ["You're doing great! 💪", "Almost there! 📍", "Hang tight! 🔍", "Stay with me! 🎯"],
    "analysis_start": ["Crunching data... 🤔", "Analyzing symptoms... 🔬", "Processing information... 💡", "Running diagnostics... 🖥️"],
    "completion": ["Analysis complete! 🎉", "Here's your report! 📊", "Diagnostics finished! ✅", "Check this out! 📈"]
}

class MedixAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.user_profiles: Dict[int, Dict] = {}
        print("🤖 MEDIX AI initialized successfully!")

    def get_wikipedia_info(self, topic: str) -> str:
        """Get medical information from Wikipedia"""
        try:
            page = wiki_wiki.page(topic)
            if page.exists():
                # Get first 500 characters for brevity
                summary = page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
                return f"📚 *Wikipedia Insight for {topic}:*\n\n{summary}\n\n🔗 *Learn more:* {page.fullurl}"
            return "ℹ️ No additional information found in medical databases."
        except:
            return "🔍 Could not fetch medical references at the moment."

    async def get_ai_diagnosis(self, symptoms: List[str], user_context: Dict) -> str:
        """Get advanced AI diagnosis with medical insights"""
        
        prompt = f"""
        You are MEDIX AI, an advanced diagnostic assistant. Analyze these symptoms with medical intelligence:

        PATIENT PROFILE:
        - Symptoms: {", ".join(symptoms)}
        - Age: {user_context.get('age', 'Not specified')}
        - Gender: {user_context.get('gender', 'Not specified')}
        - Duration: {user_context.get('duration', 'Not specified')}
        - Severity: {user_context.get('severity', 'Not specified')}

        Provide a COMPREHENSIVE medical analysis with this EXACT structure:

        🎯 QUICK ASSESSMENT
        [Brief empathetic overview - 2 lines max]

        🔍 LIKELY POSSIBILITIES (Top 3)
        • [Condition 1]: [Brief reasoning]
        • [Condition 2]: [Brief reasoning] 
        • [Condition 3]: [Brief reasoning]

        ⚠️ RED FLAGS (When to seek IMMEDIATE care)
        • [Critical symptom 1]
        • [Critical symptom 2]
        • [Critical symptom 3]

        💡 SMART RECOMMENDATIONS
        • [Immediate action 1]
        • [Self-care tip 1]
        • [Monitoring suggestion 1]

        🏥 MEDICAL GUIDANCE
        [When to see a doctor and what type of specialist]

        📊 NEXT STEPS
        [Clear action plan]

        Use medical terminology appropriately but explain in simple terms. Be empathetic but professional.
        Include emojis for better readability. Keep it concise but comprehensive.
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ I apologize, but I'm having trouble accessing my medical databases right now. Please try again in a moment or consult a healthcare provider directly for urgent concerns."

    def get_personality_phrase(self, category: str) -> str:
        """Get random personality phrase"""
        return random.choice(BOT_PERSONALITY.get(category, ["Proceeding..."]))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Interactive start command"""
        user = update.effective_user
        
        welcome_text = f"""
{random.choice(BOT_PERSONALITY['greetings'])} *{user.first_name}!*

I'm *MEDIX AI* 🤖 - Your Advanced Diagnostic Assistant!

🔬 *What I can do:*
• 🧠 AI-Powered Symptom Analysis
• 📚 Medical Database References  
• 🎯 Personalized Health Insights
• ⚡ Quick Risk Assessment
• 💡 Smart Recommendations

*Ready to begin your health assessment?* 💫
        """
        
        keyboard = [
            [KeyboardButton("🔍 Start Diagnosis"), KeyboardButton("💊 Medication Info")],
            [KeyboardButton("📚 Health Library"), KeyboardButton("🆘 Emergency Guide")],
            [KeyboardButton("ℹ️ About MEDIX AI"), KeyboardButton("🎲 Quick Tip")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def start_diagnosis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start advanced diagnosis flow"""
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {
            'symptoms': [],
            'start_time': datetime.now(),
            'step': 'symptoms'
        }
        
        # Create dynamic symptom keyboard
        keyboard = []
        for category, symptoms in SYMPTOM_DATABASE.items():
            row = [KeyboardButton(f"{category.split()[0]} {symptoms[0]}")]
            if len(symptoms) > 1:
                row.append(KeyboardButton(f"{category.split()[0]} {symptoms[1]}"))
            keyboard.append(row)
        
        keyboard.extend([
            [KeyboardButton("✅ Proceed to Analysis"), KeyboardButton("🔄 Reset Selection")],
            [KeyboardButton("🏠 Main Menu")]
        ])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        instruction = f"""
{self.get_personality_phrase('analysis_start')}

*Step 1: Symptom Selection* 🎯

Select *all* symptoms you're experiencing from the categories below.

💡 *Tip:* Choose multiple symptoms for better accuracy!

*Selected:* {len(self.user_sessions[user_id]['symptoms'])} symptoms
        """
        
        await update.message.reply_text(instruction, reply_markup=reply_markup, parse_mode='Markdown')
        return SYMPTOMS

    async def handle_symptoms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symptom selection with personality"""
        user_id = update.effective_user.id
        text = update.message.text
        session = self.user_sessions.get(user_id, {})
        
        if text == "✅ Proceed to Analysis":
            if not session.get('symptoms'):
                await update.message.reply_text(
                    "❌ Please select at least one symptom for analysis! 🎯"
                )
                return SYMPTOMS
            
            # Move to details collection
            session['step'] = 'details'
            
            age_keyboard = [
                ["👶 0-18 Years", "👨 19-35 Years"],
                ["👨‍🦳 36-55 Years", "👴 55+ Years"],
                ["🚫 Skip Personal Info"]
            ]
            reply_markup = ReplyKeyboardMarkup(age_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"{self.get_personality_phrase('encouragement')}\n\n"
                "*Step 2: Quick Profile* 👤\n\n"
                "Help me personalize your analysis (optional but recommended):",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return DETAILS
            
        elif text == "🔄 Reset Selection":
            session['symptoms'] = []
            await update.message.reply_text(
                "🔄 Selection reset! Choose your symptoms again:",
                parse_mode='Markdown'
            )
            return SYMPTOMS
            
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
            return ConversationHandler.END
            
        else:
            # Add symptom with personality
            if 'symptoms' not in session:
                session['symptoms'] = []
            
            symptom_name = ' '.join(text.split()[1:])  # Remove emoji
            if symptom_name not in session['symptoms']:
                session['symptoms'].append(symptom_name)
                await update.message.reply_text(
                    f"{self.get_personality_phrase('positive_feedback')} "
                    f"Added *{symptom_name}* to analysis!\n\n"
                    f"📋 *Selected ({len(session['symptoms'])}):* {', '.join(session['symptoms'])}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"✅ Already tracking *{symptom_name}*!\n\n"
                    f"Continue selecting or click *✅ Proceed to Analysis* when ready.",
                    parse_mode='Markdown'
                )
            
            return SYMPTOMS

    async def handle_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user details collection"""
        user_id = update.effective_user.id
        text = update.message.text
        session = self.user_sessions[user_id]
        
        if session['step'] == 'details':
            if "Years" in text:
                session['age'] = text
                
                gender_keyboard = [["👨 Male", "👩 Female"], ["⚧ Other", "🚫 Skip"]]
                reply_markup = ReplyKeyboardMarkup(gender_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "👤 *Biological Sex* (for better accuracy):",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif text in ["👨 Male", "👩 Female", "⚧ Other"]:
                session['gender'] = text
                session['step'] = 'duration'
                
                duration_keyboard = [
                    ["⏱️ <24 Hours", "🕐 1-3 Days"],
                    ["🕑 3-7 Days", "🕒 1-4 Weeks"], 
                    ["🕓 1+ Months", "❓ Not Sure"]
                ]
                reply_markup = ReplyKeyboardMarkup(duration_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "⏰ *Symptom Duration:*\nHow long have you experienced these symptoms?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif text == "🚫 Skip":
                session['step'] = 'duration'
                duration_keyboard = [
                    ["⏱️ <24 Hours", "🕐 1-3 Days"],
                    ["🕑 3-7 Days", "🕒 1-4 Weeks"],
                    ["🕓 1+ Months", "❓ Not Sure"]
                ]
                reply_markup = ReplyKeyboardMarkup(duration_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "⏰ *Symptom Duration:*\nHow long have you experienced these symptoms?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif text == "🚫 Skip Personal Info":
                session.update({'age': 'Not specified', 'gender': 'Not specified'})
                session['step'] = 'duration'
                
                duration_keyboard = [
                    ["⏱️ <24 Hours", "🕐 1-3 Days"],
                    ["🕑 3-7 Days", "🕒 1-4 Weeks"],
                    ["🕓 1+ Months", "❓ Not Sure"]
                ]
                reply_markup = ReplyKeyboardMarkup(duration_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "⏰ *Symptom Duration:*\nHow long have you experienced these symptoms?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            else:
                # Handle duration
                session['duration'] = text
                session['step'] = 'severity'
                
                severity_keyboard = [
                    ["😊 Mild (Annoying)", "😐 Moderate (Disruptive)"],
                    ["😫 Severe (Limiting)", "🚨 Critical (Emergency)"]
                ]
                reply_markup = ReplyKeyboardMarkup(severity_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "📊 *Symptom Severity:*\nHow much do symptoms affect your daily life?",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return DETAILS
                
        else:
            # Handle severity
            session['severity'] = text
            
            await update.message.reply_text(
                f"{self.get_personality_phrase('analysis_start')}\n"
                "🚀 *Starting Advanced AI Analysis...*\n\n"
                "🤖 Consulting medical databases...\n"
                "🔍 Cross-referencing symptoms...\n"
                "💡 Generating insights...",
                parse_mode='Markdown'
            )
            
            # Get AI diagnosis
            diagnosis = await self.get_ai_diagnosis(
                session['symptoms'], 
                {k: session.get(k, 'Not specified') for k in ['age', 'gender', 'duration', 'severity']}
            )
            
            # Send diagnosis
            await update.message.reply_text(
                f"{self.get_personality_phrase('completion')}\n\n"
                f"{diagnosis}\n\n"
                "💫 *MEDIX AI Analysis Complete*",
                parse_mode='Markdown'
            )
            
            # Get Wikipedia reference for first symptom
            if session['symptoms']:
                wiki_info = self.get_wikipedia_info(session['symptoms'][0])
                await update.message.reply_text(wiki_info, parse_mode='Markdown')
            
            # Show next steps
            followup_keyboard = [
                [KeyboardButton("🔍 New Diagnosis"), KeyboardButton("📚 Research More")],
                [KeyboardButton("💊 Medication Info"), KeyboardButton("🏠 Main Menu")]
            ]
            reply_markup = ReplyKeyboardMarkup(followup_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "🔄 *What would you like to do next?*",
                reply_markup=reply_markup
            )
            
            return ConversationHandler.END
        
        return DETAILS

    async def handle_health_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Health library with Wikipedia integration"""
        library_keyboard = [
            ["🤒 Common Cold", "🦠 COVID-19", "😷 Influenza"],
            ["💓 Hypertension", "🩸 Diabetes", "🧠 Migraine"],
            ["🍽️ Food Poisoning", "🫁 Asthma", "😴 Insomnia"],
            ["🏠 Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(library_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📚 *MEDIX Health Library*\n\n"
            "Select a condition to learn more from medical databases:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_medication_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Medication safety information"""
        await update.message.reply_text(
            "💊 *Medication Safety Center* 🛡️\n\n"
            "🔬 *Important Information:*\n"
            "• Always consult healthcare providers before taking medication\n"
            "• Follow prescribed dosages exactly\n"
            "• Report side effects immediately\n"
            "• Never share medications with others\n\n"
            "📞 *For specific medication questions:*\n"
            "• Consult your pharmacist\n"
            "• Contact your doctor\n"
            "• Use reputable medical sources\n\n"
            "*MEDIX AI does not prescribe medications.*",
            parse_mode='Markdown'
        )

    async def handle_emergency_guide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Emergency guidance"""
        await update.message.reply_text(
            "🆘 *EMERGENCY MEDICAL GUIDE* 🚨\n\n"
            "*IMMEDIATE ACTION REQUIRED FOR:*\n"
            "• Difficulty breathing\n"
            "• Chest pain or pressure\n"
            "• Severe bleeding\n"
            "• Sudden weakness/numbness\n"
            "• Severe allergic reaction\n"
            "• Thoughts of self-harm\n\n"
            "🚑 *TAKE THESE STEPS:*\n"
            "1. CALL LOCAL EMERGENCY NUMBER\n"
            "2. Go to nearest hospital\n"
            "3. Don't drive yourself if impaired\n\n"
            "📞 *Emergency Numbers:*\n"
            "• US: 911 • UK: 999 • EU: 112\n"
            "• India: 112 • Australia: 000\n\n"
            "*This bot cannot provide emergency care.*",
            parse_mode='Markdown'
        )

    async def handle_quick_tip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Random health tip"""
        tips = [
            "💧 *Hydration Tip:* Drink water when you wake up to kickstart metabolism!",
            "😴 *Sleep Tip:* Keep your bedroom cool (60-67°F) for better sleep quality!",
            "🏃 *Exercise Tip:* 10-minute walks after meals help regulate blood sugar!",
            "🥗 *Nutrition Tip:* Eat colorful vegetables for diverse nutrients!",
            "🧠 *Mental Health:* 5-minute meditation breaks reduce stress significantly!",
            "👀 *Eye Care:* Follow 20-20-20 rule: every 20 minutes, look 20 feet away for 20 seconds!",
            "💓 *Heart Health:* Laughter really is good medicine - it improves blood flow!",
            "🦴 *Bone Health:* Vitamin D + Calcium work better together for bone strength!"
        ]
        await update.message.reply_text(random.choice(tips), parse_mode='Markdown')

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About MEDIX AI"""
        await update.message.reply_text(
            "ℹ️ *About MEDIX AI* 🤖\n\n"
            "*Advanced Diagnostic Assistant*\n"
            "Powered by Google Gemini AI + Wikipedia Medical Database\n\n"
            "🔬 *Features:*\n"
            "• AI-Powered Symptom Analysis\n"
            "• Medical Database Integration\n"
            "• Personalized Health Insights\n"
            "• Risk Assessment Algorithms\n"
            "• Smart Recommendation Engine\n\n"
            "⚠️ *Disclaimer:*\n"
            "MEDIX AI provides informational support only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult healthcare professionals for medical concerns.\n\n"
            "💫 *Stay healthy, stay informed!*",
            parse_mode='Markdown'
        )

    async def handle_wikipedia_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Wikipedia searches from health library"""
        text = update.message.text
        if text != "🏠 Main Menu":
            await update.message.reply_text("🔍 Fetching medical information...")
            wiki_info = self.get_wikipedia_info(text)
            await update.message.reply_text(wiki_info, parse_mode='Markdown')
        else:
            await self.start_command(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all other messages"""
        text = update.message.text
        
        if text == "🔍 Start Diagnosis":
            await self.start_diagnosis(update, context)
        elif text == "📚 Health Library":
            await self.handle_health_library(update, context)
        elif text == "💊 Medication Info":
            await self.handle_medication_info(update, context)
        elif text == "🆘 Emergency Guide":
            await self.handle_emergency_guide(update, context)
        elif text == "ℹ️ About MEDIX AI":
            await self.handle_about(update, context)
        elif text == "🎲 Quick Tip":
            await self.handle_quick_tip(update, context)
        elif text in ["🤒 Common Cold", "🦠 COVID-19", "😷 Influenza", "💓 Hypertension", 
                     "🩸 Diabetes", "🧠 Migraine", "🍽️ Food Poisoning", "🫁 Asthma", "😴 Insomnia"]:
            await self.handle_wikipedia_search(update, context)
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
        else:
            await update.message.reply_text(
                "🤖 *MEDIX AI* here! I'm your advanced diagnostic assistant.\n\n"
                "Use the menu below to:\n"
                "• 🔍 Start a symptom analysis\n"
                "• 📚 Browse health information\n"
                "• 💊 Get medication safety tips\n"
                "• 🆘 Access emergency guidance\n\n"
                "How can I assist you today? 💫",
                parse_mode='Markdown'
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text(
            "🔄 Session cancelled. Ready when you are! 💫",
            reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
        )
        return ConversationHandler.END

def main():
    """Start the advanced AI bot"""
    print("🚀 Starting MEDIX AI - Advanced Diagnostic Assistant...")
    
    # Create bot instance
    medix_ai = MedixAI()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add conversation handler for diagnosis
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🔍 Start Diagnosis$'), medix_ai.start_diagnosis)
        ],
        states={
            SYMPTOMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medix_ai.handle_symptoms)
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, medix_ai.handle_details)
            ]
        },
        fallbacks=[CommandHandler('cancel', medix_ai.cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", medix_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, medix_ai.handle_message))
    
    # Start the bot
    print("✅ MEDIX AI setup completed!")
    print("🤖 Advanced diagnostic bot is running...")
    print("📱 Send /start to test the ultimate medical AI experience!")
    
    application.run_polling()

if __name__ == '__main__':
    main()
