#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Advanced Medical Diagnostic Assistant
AI-powered medical bot with Gemini AI integration and chat-based diagnosis
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
    user_agent='RAGnosisAI/1.0',
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Conversation states
CHAT_DIAGNOSIS, DETAILS = range(2)

class RagnosisAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.chat_history: Dict[int, List] = {}
        print("🤖 RAGnosis AI initialized successfully!")

    async def get_gemini_summary(self, text: str, max_length: int = 300) -> str:
        """Use Gemini to create concise, user-friendly summaries"""
        try:
            prompt = f"""
            Summarize this medical information in a clear, concise, and patient-friendly way. 
            Focus on key points that are most relevant to someone seeking health advice.
            Keep it under {max_length} words. Use simple language and include emojis for better readability.
            
            Information to summarize: {text}
            """
            
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except:
            return text[:400] + "..." if len(text) > 400 else text

    async def get_ai_chat_diagnosis(self, user_message: str, chat_history: List, user_context: Dict) -> str:
        """AI-powered chat-based diagnosis using Gemini"""
        
        # Build conversation context
        history_text = "\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in chat_history[-6:]])
        
        prompt = f"""
        You are RAGnosis AI, a friendly and empathetic medical AI assistant. You're having a conversational diagnosis chat with a user.

        USER CONTEXT:
        {user_context.get('medical_context', 'No prior context')}

        RECENT CONVERSATION:
        {history_text}

        USER'S LATEST MESSAGE:
        {user_message}

        Provide a SHORT, FRIENDLY response that:
        - 🩺 Acknowledges their concern
        - 🔍 Asks 1-2 relevant follow-up questions 
        - 💡 Offers brief, practical insight
        - 😊 Uses empathetic tone with emojis
        - 🎯 Keeps response under 150 words

        Remember: You're having a conversation, not writing a medical report. Be warm, engaging, and helpful.
        """

        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "🤖 I'm here to help! Could you tell me more about what you're experiencing? 😊"

    async def get_comprehensive_analysis(self, chat_history: List, user_context: Dict) -> str:
        """Generate final comprehensive analysis using Gemini"""
        
        conversation_summary = "\n".join([f"- {msg['user']}" for msg in chat_history])
        
        prompt = f"""
        Based on this entire conversation, provide a COMPREHENSIVE but CONCISE medical analysis:

        CONVERSATION SUMMARY:
        {conversation_summary}

        USER CONTEXT:
        Age: {user_context.get('age', 'Not specified')}
        Gender: {user_context.get('gender', 'Not specified')}

        Provide analysis in this EXACT format:

        🎯 **Quick Assessment**
        [2-3 line summary]

        🔍 **Likely Possibilities** 
        • [Condition 1] - [Brief reason]
        • [Condition 2] - [Brief reason]

        ⚠️ **When to Seek Help**
        [Specific warning signs]

        💡 **Next Steps**
        [2-3 actionable recommendations]

        Keep it UNDER 400 words total. Be empathetic but professional.
        """

        try:
            response = gemini_model.generate_content(prompt)
            return await self.get_gemini_summary(response.text, 350)
        except:
            return "🩺 Based on our chat, I recommend consulting a healthcare provider for proper evaluation. Your symptoms deserve professional attention! 💫"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Interactive AI-powered start"""
        user = update.effective_user
        
        welcome_text = f"""
👋 **Hello {user.first_name}! I'm RAGnosis AI** 🤖

Your **AI Health Companion** for:
• 🗣️ **Chat-based Diagnosis** - Talk naturally about symptoms
• 🎯 **Quick AI Analysis** - Get instant insights  
• 🩺 **First Aid Guide** - Emergency help
• 📚 **Medical Library** - Reliable information

**Choose how you'd like to start:**
        """
        
        keyboard = [
            [KeyboardButton("🗣️ Chat Diagnosis"), KeyboardButton("🎯 Quick Analysis")],
            [KeyboardButton("🩺 First Aid"), KeyboardButton("📚 Medical Info")],
            [KeyboardButton("💊 Med Safety"), KeyboardButton("🚨 Emergency")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def start_chat_diagnosis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start conversational diagnosis"""
        user_id = update.effective_user.id
        
        # Initialize chat session
        self.user_sessions[user_id] = {
            'age': 'Not specified',
            'gender': 'Not specified', 
            'medical_context': 'New conversation started'
        }
        self.chat_history[user_id] = []
        
        welcome_msg = """
🗣️ **Chat Diagnosis Mode Activated!** 🤖

💬 **Talk to me naturally about:**
• What symptoms you're feeling
• When they started  
• How they're affecting you
• Any concerns you have

🎯 **I'll:** 
• Ask relevant questions
• Provide instant insights
• Guide you toward next steps

**Just start typing - tell me what's going on!** 😊

Type `🏠 Main Menu` anytime to return.
        """
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle conversational diagnosis messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🏠 Main Menu":
            await self.start_command(update, context)
            return ConversationHandler.END
            
        if user_message == "📊 Get Analysis Report":
            # Generate comprehensive analysis
            if user_id in self.chat_history and len(self.chat_history[user_id]) > 2:
                await update.message.reply_text("🧠 **Generating your AI analysis...**")
                
                analysis = await self.get_comprehensive_analysis(
                    self.chat_history[user_id], 
                    self.user_sessions[user_id]
                )
                
                await update.message.reply_text(f"📋 **Your AI Health Analysis**\n\n{analysis}", parse_mode='Markdown')
                
                # Offer next steps
                next_keyboard = [
                    [KeyboardButton("🗣️ Continue Chat"), KeyboardButton("🎯 New Analysis")],
                    [KeyboardButton("🩺 First Aid"), KeyboardButton("🏠 Main Menu")]
                ]
                reply_markup = ReplyKeyboardMarkup(next_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "🔄 **What would you like to do next?**",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text("💬 **Please chat with me a bit more so I can provide a better analysis!**")
                return CHAT_DIAGNOSIS

        # Store user message
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []
            
        # Get AI response
        await update.message.reply_chat_action("typing")
        ai_response = await self.get_ai_chat_diagnosis(
            user_message, 
            self.chat_history[user_id],
            self.user_sessions[user_id]
        )
        
        # Store conversation
        self.chat_history[user_id].append({
            'user': user_message,
            'ai': ai_response
        })
        
        # Add quick actions after a few messages
        if len(self.chat_history[user_id]) >= 3:
            quick_keyboard = [
                [KeyboardButton("📊 Get Analysis Report"), KeyboardButton("🗣️ Continue Chat")],
                [KeyboardButton("🩺 First Aid"), KeyboardButton("🏠 Main Menu")]
            ]
            reply_markup = ReplyKeyboardMarkup(quick_keyboard, resize_keyboard=True)
            await update.message.reply_text(ai_response, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(ai_response, parse_mode='Markdown')
        
        return CHAT_DIAGNOSIS

    async def quick_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick symptom analysis"""
        keyboard = [
            [KeyboardButton("🤒 Fever + Cough"), KeyboardButton("🤕 Headache + Dizziness")],
            [KeyboardButton("🤢 Nausea + Vomiting"), KeyboardButton("💓 Chest Pain")],
            [KeyboardButton("🫁 Breathing Issues"), KeyboardButton("🔍 Other Symptoms")],
            [KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🎯 **Quick Symptom Analysis**\n\n"
            "Select common symptom combinations or describe your own:\n\n"
            "💡 *I'll provide instant AI-powered insights*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_quick_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quick analysis selections"""
        user_input = update.message.text
        
        if user_input == "🏠 Main Menu":
            await self.start_command(update, context)
            return
            
        # Use Gemini for quick analysis
        prompt = f"""
        Provide a QUICK, CONCISE medical insight for someone experiencing: {user_input}
        
        Format your response:
        🎯 **Quick Insight** [1-2 lines]
        💡 **Suggestions** [2-3 bullet points]
        ⚠️ **Watch For** [1-2 warning signs]
        
        Keep it under 150 words. Use simple language with emojis.
        """
        
        await update.message.reply_chat_action("typing")
        try:
            response = gemini_model.generate_content(prompt)
            analysis = response.text.strip()
        except:
            analysis = "🩺 Based on your symptoms, I recommend monitoring closely and consulting a healthcare provider if symptoms persist or worsen. 💫"
        
        await update.message.reply_text(
            f"🔍 **Quick Analysis for {user_input}**\n\n{analysis}",
            parse_mode='Markdown'
        )

    async def handle_first_aid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """First Aid Guide"""
        keyboard = [
            [KeyboardButton("🤕 Cuts & Bleeding"), KeyboardButton("🔥 Burns")],
            [KeyboardButton("💓 CPR Steps"), KeyboardButton("🤧 Choking")],
            [KeyboardButton("🐝 Allergic Reaction"), KeyboardButton("🦴 Fractures")],
            [KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🩺 **First Aid & Emergency Guide**\n\n"
            "Select a topic for immediate guidance:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_medical_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Medical Information"""
        keyboard = [
            [KeyboardButton("🦠 COVID-19 Info"), KeyboardButton("😷 Flu Guide")],
            [KeyboardButton("💓 Heart Health"), KeyboardButton("🩸 Diabetes")],
            [KeyboardButton("🧠 Mental Health"), KeyboardButton("🍽️ Nutrition")],
            [KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📚 **Medical Information Center**\n\n"
            "Choose a health topic to learn more:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_med_safety(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Medication Safety"""
        safety_info = """
💊 **Medication Safety Guide** 🛡️

🔬 **Essential Safety Tips:**
• 🩺 Always consult doctors before taking new meds
• 📋 Follow prescribed dosages exactly
• ⚠️ Report side effects immediately
• 🔒 Never share medications
• 📚 Check drug interactions

🚨 **Emergency Signs:**
• Severe allergic reactions
• Difficulty breathing
• Chest pain
• Severe dizziness

📞 **Contact healthcare providers for any concerns!**
        """
        
        await update.message.reply_text(safety_info, parse_mode='Markdown')

    async def handle_emergency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Emergency Guide"""
        emergency_info = """
🚨 **EMERGENCY GUIDE** 🚑

🆘 **IMMEDIATE ACTION NEEDED FOR:**
• 🫁 Difficulty breathing
• 💓 Chest pain/pressure
• 🩸 Severe bleeding
• 🧠 Sudden weakness/numbness
• 🔥 Severe allergic reaction

📞 **EMERGENCY NUMBERS:**
• US: 911 • UK: 999 • EU: 112
• India: 112 • Australia: 000

🏥 **Go to nearest hospital immediately!**

*RAGnosis AI supports but cannot replace emergency care.*
        """
        
        await update.message.reply_text(emergency_info, parse_mode='Markdown')

    async def handle_wikipedia_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle medical info searches with Gemini summaries"""
        topic = update.message.text.replace(" Info", "").replace(" Guide", "")
        
        if topic == "🏠 Main Menu":
            await self.start_command(update, context)
            return
            
        await update.message.reply_text(f"🔍 **Searching {topic} info...**")
        
        try:
            # Get Wikipedia info
            page = wiki_wiki.page(topic)
            if page.exists():
                raw_info = page.summary[:800] if len(page.summary) > 800 else page.summary
                
                # Use Gemini to create user-friendly summary
                summary = await self.get_gemini_summary(raw_info)
                
                response = f"📚 **{topic}**\n\n{summary}\n\n🔗 *Learn more: {page.fullurl}*"
            else:
                response = f"ℹ️ **{topic}**\n\nFor detailed information, consult healthcare professionals or reliable medical sources. 🩺"
        except:
            response = f"📚 **{topic}**\n\nMedical information currently unavailable. Please consult healthcare providers. 🩺"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main message handler"""
        text = update.message.text
        
        if text == "🗣️ Chat Diagnosis":
            await self.start_chat_diagnosis(update, context)
        elif text == "🎯 Quick Analysis":
            await self.quick_analysis(update, context)
        elif text == "🩺 First Aid":
            await self.handle_first_aid(update, context)
        elif text == "📚 Medical Info":
            await self.handle_medical_info(update, context)
        elif text == "💊 Med Safety":
            await self.handle_med_safety(update, context)
        elif text == "🚨 Emergency":
            await self.handle_emergency(update, context)
        elif text in ["🤒 Fever + Cough", "🤕 Headache + Dizziness", "🤢 Nausea + Vomiting", 
                     "💓 Chest Pain", "🫁 Breathing Issues", "🔍 Other Symptoms"]:
            await self.handle_quick_analysis(update, context)
        elif text in ["🤕 Cuts & Bleeding", "🔥 Burns", "💓 CPR Steps", "🤧 Choking", 
                     "🐝 Allergic Reaction", "🦴 Fractures"]:
            await self.handle_wikipedia_search(update, context)
        elif text in ["🦠 COVID-19 Info", "😷 Flu Guide", "💓 Heart Health", "🩸 Diabetes",
                     "🧠 Mental Health", "🍽️ Nutrition"]:
            await self.handle_wikipedia_search(update, context)
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
        else:
            # Default response for unexpected messages
            await update.message.reply_text(
                "🤖 **RAGnosis AI** - Your Health Companion!\n\n"
                "Choose an option below or type /start to see all features! 💫",
                parse_mode='Markdown'
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text(
            "🔄 Chat ended. Ready for your next health inquiry! 💫",
            reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
        )
        return ConversationHandler.END

def main():
    """Start the enhanced RAGnosis AI"""
    print("🚀 Starting Enhanced RAGnosis AI...")
    
    ragnosis_ai = RagnosisAI()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler for chat diagnosis
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🗣️ Chat Diagnosis$'), ragnosis_ai.start_chat_diagnosis)
        ],
        states={
            CHAT_DIAGNOSIS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_chat_message)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex('^🏠 Main Menu$'), ragnosis_ai.cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_message))
    
    print("✅ Enhanced RAGnosis AI ready!")
    print("🤖 Features: Chat Diagnosis + Quick Analysis + Gemini AI")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
