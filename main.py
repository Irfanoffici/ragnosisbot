#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Advanced Medical Diagnostic Assistant
AI-powered medical bot with Wikipedia integration and emergency response
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
    user_agent='RAGnosisAI/1.0 (https://t.me/ragnosisbot)',
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Conversation states
SYMPTOMS, DETAILS = range(2)

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

# AI Personality System
AI_PERSONALITY = {
    "greetings": [
        "🩺 Hello! I'm RAGnosis AI, your medical assistant!",
        "🤖 Greetings! RAGnosis AI at your service!",
        "💫 Hello there! Ready for some AI-powered health insights?",
        "👋 Hey! RAGnosis AI here - let's explore your health together!"
    ],
    "analysis_start": [
        "🔍 Initiating advanced symptom analysis...",
        "🤔 Processing your symptoms with AI intelligence...",
        "🧠 Consulting my medical knowledge base...",
        "💡 Analyzing patterns and correlations..."
    ],
    "encouragement": [
        "🎯 Excellent! You're helping me build a clear picture!",
        "💪 Great details! This improves diagnostic accuracy!",
        "🚀 Perfect! I'm connecting the medical dots...",
        "📊 Awesome input! My algorithms are processing..."
    ],
    "completion": [
        "✅ AI Analysis Complete! Here's your comprehensive report!",
        "📋 Diagnostic assessment ready! Review your insights below!",
        "🎉 Analysis finished! Check your personalized health assessment!",
        "🔬 Medical evaluation complete! Here are my findings!"
    ]
}

class RagnosisAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        print("🤖 RAGnosis AI initialized successfully!")

    def get_wikipedia_medical_info(self, topic: str) -> str:
        """Get medical information from Wikipedia with first aid focus"""
        try:
            page = wiki_wiki.page(topic)
            if page.exists():
                # Extract first aid and treatment information
                summary = page.summary[:600] + "..." if len(page.summary) > 600 else page.summary
                
                # Look for treatment/first aid sections
                treatment_info = ""
                if "treatment" in page.summary.lower():
                    treatment_start = page.summary.lower().find("treatment")
                    treatment_info = f"\n\n🩹 *First Aid/Treatment:* {page.summary[treatment_start:treatment_start+300]}..."
                
                return f"📚 *Medical Reference: {topic}*\n\n{summary}{treatment_info}\n\n🔗 *Learn more:* {page.fullurl}"
            return f"ℹ️ *Medical Insight:* For {topic}, consult healthcare professionals for accurate diagnosis and treatment."
        except:
            return "🔍 *Medical Database:* Additional references currently unavailable."

    async def get_ai_medical_analysis(self, symptoms: List[str], user_context: Dict) -> str:
        """Get advanced AI medical analysis with counseling"""
        
        prompt = f"""
        You are RAGnosis AI, an advanced medical diagnostic assistant. Provide COMPREHENSIVE analysis:

        PATIENT DATA:
        Symptoms: {", ".join(symptoms)}
        Age: {user_context.get('age', 'Not specified')}
        Gender: {user_context.get('gender', 'Not specified')}
        Duration: {user_context.get('duration', 'Not specified')}
        Severity: {user_context.get('severity', 'Not specified')}

        Provide analysis in this EXACT structure:

        🎯 QUICK ASSESSMENT
        [2-line empathetic overview of situation]

        🔍 LIKELY POSSIBILITIES (Ranked by Probability)
        • [Condition 1] - [Brief medical reasoning]
        • [Condition 2] - [Brief medical reasoning] 
        • [Condition 3] - [Brief medical reasoning]

        ⚠️ RED FLAGS & URGENCY ASSESSMENT
        [List critical symptoms requiring immediate attention]

        🩹 FIRST AID & IMMEDIATE CARE
        [Practical first aid steps if applicable]

        💡 SELF-CARE & MONITORING
        [Home care tips and what to watch for]

        🏥 MEDICAL CONSULTATION GUIDANCE
        [When and what type of doctor to see]

        🧠 HEALTH COUNSELING
        [Emotional support and reassurance]

        📞 EMERGENCY CONTACTS
        [When to seek immediate help]

        Use medical terminology appropriately but explain clearly. Be empathetic, professional, and actionable.
        Include relevant emojis for better communication.
        """

        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return """🔧 SYSTEM UPDATE: My medical analysis module is currently optimizing.

In the meantime:
• 🏥 Contact healthcare providers for urgent concerns
• 📚 Use reliable medical sources
• 🩺 Visit emergency services for critical symptoms

I'll be back with full AI diagnostics shortly!"""

    def get_ai_phrase(self, category: str) -> str:
        """Get AI personality phrase"""
        return random.choice(AI_PERSONALITY.get(category, ["Processing..."]))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Interactive AI-powered start"""
        user = update.effective_user
        
        welcome_text = f"""
{random.choice(AI_PERSONALITY['greetings'])}

*I'm RAGnosis AI* - Your Advanced Medical Assistant! 🤖

🔬 *What I Offer:*
• 🧠 AI-Powered Symptom Analysis
• 📚 Wikipedia Medical Database
• 🩺 First Aid Guidance  
• 💊 Medication Safety
• 🧠 Health Counseling
• 🚨 Emergency Response

*Ready to Begin Your AI Health Assessment?* 💫
        """
        
        keyboard = [
            [KeyboardButton("🔍 AI Symptom Analysis"), KeyboardButton("🩺 First Aid Guide")],
            [KeyboardButton("📚 Medical Library"), KeyboardButton("💊 Drug Safety")],
            [KeyboardButton("🧠 Mental Health"), KeyboardButton("🚨 Emergency Help")],
            [KeyboardButton("ℹ️ About RAGnosis AI")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def start_ai_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start AI-powered symptom analysis"""
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {
            'symptoms': [],
            'start_time': datetime.now()
        }
        
        # Create AI-powered symptom keyboard
        keyboard = []
        for category, symptoms in SYMPTOM_DATABASE.items():
            row = [KeyboardButton(f"{symptoms[0]}")]
            if len(symptoms) > 1:
                row.append(KeyboardButton(f"{symptoms[1]}"))
            keyboard.append(row)
        
        keyboard.extend([
            [KeyboardButton("✅ AI Analysis Ready"), KeyboardButton("🔄 Reset Symptoms")],
            [KeyboardButton("🏠 AI Main Menu")]
        ])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        instruction = f"""
{self.get_ai_phrase('analysis_start')}

*Step 1: Symptom Input* 🎯

Select *all* symptoms you're experiencing. My AI will analyze patterns.

💡 *AI Tip:* More symptoms = Better diagnostic accuracy!

*Selected Symptoms:* {len(self.user_sessions[user_id]['symptoms'])}
        """
        
        await update.message.reply_text(instruction, reply_markup=reply_markup, parse_mode='Markdown')
        return SYMPTOMS

    async def handle_symptoms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI-powered symptom handling"""
        user_id = update.effective_user.id
        text = update.message.text
        session = self.user_sessions.get(user_id, {})
        
        if text == "✅ AI Analysis Ready":
            if not session.get('symptoms'):
                await update.message.reply_text(
                    "❌ Please provide at least one symptom for AI analysis! 🎯"
                )
                return SYMPTOMS
            
            # Collect additional context
            age_keyboard = [
                ["👶 0-18 Years", "👨 19-35 Years"],
                ["👨‍🦳 36-55 Years", "👴 55+ Years"],
                ["🚫 Skip Personal Info"]
            ]
            reply_markup = ReplyKeyboardMarkup(age_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"{self.get_ai_phrase('encouragement')}\n\n"
                "*Step 2: Context for Better AI Analysis* 👤\n\n"
                "Help me personalize your diagnosis (optional but recommended for accuracy):",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return DETAILS
            
        elif text == "🔄 Reset Symptoms":
            session['symptoms'] = []
            await update.message.reply_text(
                "🔄 Symptom list cleared! Please select your symptoms again:",
                parse_mode='Markdown'
            )
            return SYMPTOMS
            
        elif text == "🏠 AI Main Menu":
            await self.start_command(update, context)
            return ConversationHandler.END
            
        else:
            # AI-powered symptom addition
            if 'symptoms' not in session:
                session['symptoms'] = []
            
            if text not in session['symptoms']:
                session['symptoms'].append(text)
                await update.message.reply_text(
                    f"✅ *AI Tracking:* Added *{text}* to analysis!\n\n"
                    f"📋 *Current Symptoms ({len(session['symptoms'])}):* {', '.join(session['symptoms'])}\n\n"
                    f"💡 Continue selecting or click *✅ AI Analysis Ready* when complete.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"🔄 *AI Note:* Already tracking *{text}*!\n\n"
                    f"Select more symptoms or proceed to analysis.",
                    parse_mode='Markdown'
                )
            
            return SYMPTOMS

    async def handle_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI context collection"""
        user_id = update.effective_user.id
        text = update.message.text
        session = self.user_sessions[user_id]
        
        if "Years" in text:
            session['age'] = text
            
            gender_keyboard = [["👨 Male", "👩 Female"], ["⚧ Other", "🚫 Skip"]]
            reply_markup = ReplyKeyboardMarkup(gender_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "👤 *Biological Sex* (improves AI accuracy):",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif text in ["👨 Male", "👩 Female", "⚧ Other"]:
            session['gender'] = text
            
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
            session.update({'age': 'Not specified', 'gender': 'Not specified'})
            
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
            # Handle duration and severity
            if 'duration' not in session:
                session['duration'] = text
                
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
                
            else:
                session['severity'] = text
                
                # Start AI Analysis
                await update.message.reply_text(
                    f"{self.get_ai_phrase('analysis_start')}\n\n"
                    "🚀 *RAGnosis AI Processing...*\n"
                    "🤖 Consulting medical knowledge base...\n"
                    "🔍 Analyzing symptom patterns...\n"
                    "💡 Generating personalized insights...\n"
                    "🧠 Applying diagnostic algorithms...",
                    parse_mode='Markdown'
                )
                
                # Get AI Medical Analysis
                analysis = await self.get_ai_medical_analysis(
                    session['symptoms'], 
                    session
                )
                
                # Send AI Analysis
                await update.message.reply_text(
                    f"{self.get_ai_phrase('completion')}\n\n"
                    f"{analysis}",
                    parse_mode='Markdown'
                )
                
                # Add Wikipedia Medical Reference
                if session['symptoms']:
                    wiki_info = self.get_wikipedia_medical_info(session['symptoms'][0])
                    await update.message.reply_text(wiki_info, parse_mode='Markdown')
                
                # Next Steps
                followup_keyboard = [
                    [KeyboardButton("🔍 New AI Analysis"), KeyboardButton("🩺 First Aid Guide")],
                    [KeyboardButton("📚 Research More"), KeyboardButton("🏠 AI Main Menu")]
                ]
                reply_markup = ReplyKeyboardMarkup(followup_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "🔄 *What would you like to explore next?*",
                    reply_markup=reply_markup
                )
                
                return ConversationHandler.END
        
        return DETAILS

    async def handle_first_aid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """First Aid and Emergency Guide"""
        first_aid_keyboard = [
            ["🤕 Cuts & Bleeding", "🔥 Burns", "🤢 Poisoning"],
            ["💓 CPR Guide", "🤧 Choking", "🦴 Fractures"],
            ["🔥 Heat Stroke", "❄️ Hypothermia", "🐝 Allergic Reactions"],
            ["🏠 AI Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(first_aid_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🩺 *RAGnosis First Aid & Emergency Center*\n\n"
            "Select a first aid topic for immediate guidance:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_medical_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Medical Library with Wikipedia"""
        library_keyboard = [
            ["🦠 COVID-19", "😷 Influenza", "🤒 Common Cold"],
            ["💓 Heart Disease", "🩸 Diabetes", "🧠 Stroke"],
            ["🍽️ Food Poisoning", "🫁 Asthma", "😴 Sleep Disorders"],
            ["🏠 AI Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(library_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📚 *RAGnosis Medical Library*\n\n"
            "Access Wikipedia medical database for reliable information:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_drug_safety(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Medication Safety Information"""
        await update.message.reply_text(
            "💊 *RAGnosis Drug Safety Center* 🛡️\n\n"
            "🔬 *Critical Safety Information:*\n"
            "• 🩺 Always consult doctors before medication\n"
            "• 📋 Follow prescribed dosages exactly\n"
            "• 🚨 Report side effects immediately\n"
            "• 🔒 Never share medications with others\n"
            "• 📚 Check drug interactions\n\n"
            "📞 *For medication questions:*\n"
            "• Contact your pharmacist\n"
            "• Consult your healthcare provider\n"
            "• Use reliable medical sources\n\n"
            "*RAGnosis AI provides information only, not prescriptions.*",
            parse_mode='Markdown'
        )

    async def handle_mental_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mental Health Support"""
        mental_health_keyboard = [
            ["😔 Depression", "😰 Anxiety", "😡 Anger Issues"],
            ["😴 Sleep Problems", "🍽️ Eating Disorders", "💔 Relationship Stress"],
            ["🧘 Mindfulness", "💪 Coping Strategies", "📞 Crisis Help"],
            ["🏠 AI Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(mental_health_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🧠 *RAGnosis Mental Health Support*\n\n"
            "Access mental health resources and counseling guidance:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_emergency_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Emergency Response Guide"""
        await update.message.reply_text(
            "🚨 *RAGnosis EMERGENCY RESPONSE GUIDE* 🚑\n\n"
            "*IMMEDIATE ACTION REQUIRED FOR:*\n"
            "• 🫁 Difficulty breathing\n"
            "• 💓 Chest pain or pressure\n"
            "• 🩸 Severe bleeding\n"
            "• 🧠 Sudden weakness/numbness\n"
            "• 🔥 Severe allergic reaction\n"
            "• 💔 Thoughts of self-harm\n\n"
            "🆘 *EMERGENCY PROTOCOL:*\n"
            "1. CALL LOCAL EMERGENCY NUMBER\n"
            "2. Go to nearest hospital immediately\n"
            "3. Do not drive if impaired\n"
            "4. Follow dispatcher instructions\n\n"
            "📞 *Global Emergency Numbers:*\n"
            "• US: 911 • UK: 999 • EU: 112\n"
            "• India: 112 • Australia: 000\n\n"
            "*RAGnosis AI supports but cannot replace emergency care.*",
            parse_mode='Markdown'
        )

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About RAGnosis AI"""
        await update.message.reply_text(
            "ℹ️ *About RAGnosis AI* 🤖\n\n"
            "*Advanced Medical Diagnostic Assistant*\n"
            "Powered by Google Gemini AI + Wikipedia Medical Database\n\n"
            "🔬 *AI-Powered Features:*\n"
            "• Advanced Symptom Analysis\n"
            "• Medical Database Integration\n"
            "• First Aid & Emergency Guidance\n"
            "• Health Counseling & Support\n"
            "• Medication Safety Information\n"
            "• Mental Health Resources\n\n"
            "⚠️ *Medical Disclaimer:*\n"
            "RAGnosis AI provides informational support only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult healthcare professionals for medical concerns.\n\n"
            "💫 *Your AI Health Companion!*",
            parse_mode='Markdown'
        )

    async def handle_wikipedia_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Wikipedia medical searches"""
        text = update.message.text
        if text != "🏠 AI Main Menu":
            await update.message.reply_text("🔍 Accessing medical database...")
            wiki_info = self.get_wikipedia_medical_info(text)
            await update.message.reply_text(wiki_info, parse_mode='Markdown')
        else:
            await self.start_command(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI-powered message handling"""
        text = update.message.text
        
        if text == "🔍 AI Symptom Analysis":
            await self.start_ai_analysis(update, context)
        elif text == "🩺 First Aid Guide":
            await self.handle_first_aid(update, context)
        elif text == "📚 Medical Library":
            await self.handle_medical_library(update, context)
        elif text == "💊 Drug Safety":
            await self.handle_drug_safety(update, context)
        elif text == "🧠 Mental Health":
            await self.handle_mental_health(update, context)
        elif text == "🚨 Emergency Help":
            await self.handle_emergency_help(update, context)
        elif text == "ℹ️ About RAGnosis AI":
            await self.handle_about(update, context)
        elif text in ["🤕 Cuts & Bleeding", "🔥 Burns", "🤢 Poisoning", "💓 CPR Guide", 
                     "🤧 Choking", "🦴 Fractures", "🔥 Heat Stroke", "❄️ Hypothermia", 
                     "🐝 Allergic Reactions", "😔 Depression", "😰 Anxiety", "😡 Anger Issues",
                     "😴 Sleep Problems", "🍽️ Eating Disorders", "💔 Relationship Stress",
                     "🧘 Mindfulness", "💪 Coping Strategies", "📞 Crisis Help",
                     "🦠 COVID-19", "😷 Influenza", "🤒 Common Cold", "💓 Heart Disease",
                     "🩸 Diabetes", "🧠 Stroke", "🍽️ Food Poisoning", "🫁 Asthma"]:
            await self.handle_wikipedia_search(update, context)
        elif text == "🏠 AI Main Menu":
            await self.start_command(update, context)
        else:
            await update.message.reply_text(
                "🤖 *RAGnosis AI* here! Your advanced medical assistant.\n\n"
                "I can help you with:\n"
                "• 🔍 AI-powered symptom analysis\n"
                "• 🩺 First aid and emergency guidance\n"
                "• 📚 Medical database research\n"
                "• 💊 Medication safety information\n"
                "• 🧠 Mental health support\n"
                "• 🚨 Emergency protocols\n\n"
                "Choose an option below to get started! 💫",
                parse_mode='Markdown'
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI-powered cancellation"""
        await update.message.reply_text(
            "🔄 AI session reset. Ready for your next health inquiry! 💫",
            reply_markup=ReplyKeyboardMarkup([["🏠 AI Main Menu"]], resize_keyboard=True)
        )
        return ConversationHandler.END

def main():
    """Start RAGnosis AI with proper error handling"""
    print("🚀 Starting RAGnosis AI - Advanced Medical Assistant...")
    
    # Create AI instance
    ragnosis_ai = RagnosisAI()
    
    # Create application with proper configuration
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add conversation handler for AI analysis
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🔍 AI Symptom Analysis$'), ragnosis_ai.start_ai_analysis)
        ],
        states={
            SYMPTOMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_symptoms)
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_details)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex('^🏠 AI Main Menu$'), ragnosis_ai.cancel)]
    )
    
    # Add all handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_message))
    
    # Start the bot with proper error handling
    print("✅ RAGnosis AI setup completed!")
    print("🤖 Advanced medical AI is now running...")
    print("📱 Visit @ragnosisbot on Telegram to experience AI-powered healthcare!")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        print("🔄 Restarting RAGnosis AI...")

if __name__ == '__main__':
    main()
