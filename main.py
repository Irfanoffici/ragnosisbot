#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Advanced Medical Diagnostic Assistant
Fixed chat-based diagnosis with proper conversation handling
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
CHAT_DIAGNOSIS = 1

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

    async def get_ai_chat_response(self, user_message: str, chat_history: List, user_context: Dict) -> str:
        """AI-powered chat response using conversation context"""
        
        # Build conversation context for Gemini
        conversation_context = ""
        if chat_history:
            conversation_context = "Previous conversation:\n"
            for msg in chat_history[-4:]:  # Last 4 exchanges for context
                conversation_context += f"User: {msg['user']}\n"
                conversation_context += f"AI: {msg['ai']}\n\n"
        
        prompt = f"""
        You are RAGnosis AI, a friendly and empathetic medical AI assistant. You're having a conversational diagnosis chat with a user.

        USER CONTEXT:
        Age: {user_context.get('age', 'Not specified')}
        Gender: {user_context.get('gender', 'Not specified')}
        Medical Background: {user_context.get('medical_context', 'No prior context')}

        {conversation_context}
        
        USER'S LATEST MESSAGE:
        "{user_message}"

        Provide a natural, conversational response that:
        - 🩺 Shows empathy and understanding
        - 🔍 Asks relevant follow-up questions to gather more information
        - 💡 Offers brief, practical medical insights
        - 😊 Uses warm, friendly tone with appropriate emojis
        - 🎯 Keeps response concise (2-4 sentences)

        Remember: You're having a flowing conversation. Build on previous messages and guide the user toward better understanding their symptoms.

        Current conversation flow: Symptom discussion -> Detailed questioning -> Analysis -> Recommendations
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "🤖 I'm here to listen! Could you tell me more about what you're experiencing? 😊"

    async def get_comprehensive_analysis(self, chat_history: List, user_context: Dict) -> str:
        """Generate final comprehensive analysis using Gemini"""
        
        if not chat_history:
            return "💬 Please chat with me about your symptoms first so I can provide a proper analysis! 🩺"
        
        # Extract all user messages for analysis
        user_symptoms = "\n".join([f"- {msg['user']}" for msg in chat_history if 'user' in msg])
        
        prompt = f"""
        Based on this entire health conversation, provide a COMPREHENSIVE but CONCISE medical analysis:

        USER'S REPORTED SYMPTOMS:
        {user_symptoms}

        USER CONTEXT:
        Age: {user_context.get('age', 'Not specified')}
        Gender: {user_context.get('gender', 'Not specified')}

        Provide analysis in this EXACT format:

        🎯 **Quick Assessment**
        [2-3 line empathetic summary]

        🔍 **Possible Considerations** 
        • [Condition 1] - [Brief medical reasoning]
        • [Condition 2] - [Brief medical reasoning]

        ⚠️ **When to Seek Help**
        [Specific warning signs to watch for]

        💡 **Recommended Next Steps**
        [2-3 actionable recommendations]

        Keep it UNDER 300 words total. Be empathetic but professional. Use simple language with emojis.
        """

        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except:
            return """🩺 **Based on our conversation, here's my assessment:**

🎯 **Quick Assessment**
I've reviewed your symptoms and recommend professional medical consultation for proper evaluation.

⚠️ **When to Seek Help**
- Symptoms worsening or not improving
- New concerning symptoms develop
- Difficulty with daily activities

💡 **Recommended Next Steps**
1. Schedule appointment with healthcare provider
2. Monitor symptoms closely
3. Follow up if condition changes"""

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
        return ConversationHandler.END

    async def start_chat_diagnosis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start conversational diagnosis"""
        user_id = update.effective_user.id
        
        # Initialize or reset chat session
        self.user_sessions[user_id] = {
            'age': 'Not specified',
            'gender': 'Not specified', 
            'medical_context': 'New conversation started',
            'chat_start_time': datetime.now()
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

Type `🏠 Main Menu` anytime to return or `📊 Get Analysis` when ready for full report.
        """
        
        keyboard = [
            [KeyboardButton("📊 Get Analysis"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle conversational diagnosis messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Check if user wants to end chat
        if user_message == "🏠 Main Menu":
            await self.end_chat_session(update, user_id)
            return ConversationHandler.END
            
        # Check if user wants analysis report
        if user_message == "📊 Get Analysis":
            return await self.generate_analysis_report(update, user_id)
        
        # Initialize chat history if not exists
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []
        
        # Show typing action
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(1)  # Simulate thinking
        
        # Get AI response based on conversation context
        ai_response = await self.get_ai_chat_response(
            user_message, 
            self.chat_history[user_id],
            self.user_sessions.get(user_id, {})
        )
        
        # Store conversation
        self.chat_history[user_id].append({
            'user': user_message,
            'ai': ai_response,
            'timestamp': datetime.now()
        })
        
        # Create response keyboard
        keyboard = [
            [KeyboardButton("📊 Get Analysis"), KeyboardButton("🗣️ Continue Chat")],
            [KeyboardButton("🩺 First Aid"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Send AI response
        await update.message.reply_text(ai_response, reply_markup=reply_markup, parse_mode='Markdown')
        
        return CHAT_DIAGNOSIS

    async def generate_analysis_report(self, update: Update, user_id: int):
        """Generate and send comprehensive analysis report"""
        if user_id not in self.chat_history or len(self.chat_history[user_id]) < 1:
            await update.message.reply_text(
                "💬 **Please chat with me about your symptoms first so I can provide a proper analysis!** 🩺"
            )
            return CHAT_DIAGNOSIS
        
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(2)  # Simulate analysis time
        
        # Generate comprehensive analysis
        analysis = await self.get_comprehensive_analysis(
            self.chat_history[user_id], 
            self.user_sessions.get(user_id, {})
        )
        
        # Send analysis
        await update.message.reply_text(
            f"📋 **Your AI Health Analysis Report** 📊\n\n{analysis}",
            parse_mode='Markdown'
        )
        
        # Offer next steps
        next_keyboard = [
            [KeyboardButton("🗣️ New Chat"), KeyboardButton("🎯 Quick Analysis")],
            [KeyboardButton("🩺 First Aid"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(next_keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🔄 **What would you like to do next?**",
            reply_markup=reply_markup
        )
        
        # Clear chat history for this session
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
        
        return ConversationHandler.END

    async def end_chat_session(self, update: Update, user_id: int):
        """Properly end chat session"""
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
        
        await update.message.reply_text(
            "🔄 **Chat session ended.** Ready for your next health inquiry! 💫",
            reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
        )

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
            
        if user_input == "🔍 Other Symptoms":
            await update.message.reply_text(
                "💬 **Please describe your symptoms in your own words:**\n\n"
                "Example: 'I have been having stomach pain and fever for 2 days'"
            )
            return
            
        # Use Gemini for quick analysis
        prompt = f"""
        Provide a QUICK, CONCISE medical insight for someone experiencing: {user_input}
        
        Format your response:
        🎯 **Quick Insight** [1-2 lines summary]
        💡 **Suggestions** [2-3 practical tips]
        ⚠️ **Watch For** [1-2 specific warning signs]
        
        Keep it under 150 words. Use simple language with emojis. Be empathetic.
        """
        
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(1)
        
        try:
            response = gemini_model.generate_content(prompt)
            analysis = response.text.strip()
        except:
            analysis = """🩺 **Quick Insight**
Based on your symptoms, monitoring is recommended.

💡 **Suggestions**
• Rest and hydrate well
• Monitor symptom changes

⚠️ **Watch For**
• Worsening symptoms
• Difficulty breathing"""

        keyboard = [
            [KeyboardButton("🗣️ Chat Diagnosis"), KeyboardButton("🎯 New Analysis")],
            [KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🔍 **Quick Analysis for {user_input}**\n\n{analysis}",
            reply_markup=reply_markup,
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
            return await self.start_chat_diagnosis(update, context)
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
        elif text in ["🗣️ Continue Chat", "🗣️ New Chat"]:
            await self.start_chat_diagnosis(update, context)
        elif text == "🎯 New Analysis":
            await self.quick_analysis(update, context)
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
        else:
            # If we're in conversation mode, handle as chat message
            if context.user_data and 'conversation' in context.user_data:
                return await self.handle_chat_message(update, context)
            else:
                # Default response for unexpected messages
                await update.message.reply_text(
                    "🤖 **RAGnosis AI** - Your Health Companion!\n\n"
                    "Choose an option below or try `🗣️ Chat Diagnosis` to talk about symptoms! 💫",
                    parse_mode='Markdown'
                )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        user_id = update.effective_user.id
        await self.end_chat_session(update, user_id)
        return ConversationHandler.END

def main():
    """Start the fixed RAGnosis AI"""
    print("🚀 Starting Fixed RAGnosis AI with Chat Functionality...")
    
    ragnosis_ai = RagnosisAI()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler for chat diagnosis - FIXED
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🗣️ Chat Diagnosis$'), ragnosis_ai.start_chat_diagnosis),
            MessageHandler(filters.Regex('^🗣️ New Chat$'), ragnosis_ai.start_chat_diagnosis),
            MessageHandler(filters.Regex('^🗣️ Continue Chat$'), ragnosis_ai.start_chat_diagnosis)
        ],
        states={
            CHAT_DIAGNOSIS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    ragnosis_ai.handle_chat_message
                )
            ],
        },
        fallbacks=[
            CommandHandler('cancel', ragnosis_ai.cancel),
            MessageHandler(filters.Regex('^🏠 Main Menu$'), ragnosis_ai.cancel),
            MessageHandler(filters.Regex('^📊 Get Analysis$'), ragnosis_ai.handle_chat_message)
        ],
        allow_reentry=True
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_message))
    
    print("✅ Fixed RAGnosis AI ready!")
    print("🤖 Chat functionality now working properly!")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()