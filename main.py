#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Ultimate Medical Companion
Fully-featured medical AI with intelligent chat, memory, and advanced diagnostics
"""

import os
import asyncio
import random
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.error import Conflict, NetworkError
import google.generativeai as genai
from dotenv import load_dotenv
import wikipediaapi

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
    user_agent='RagnosisAI/2.0',
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Conversation states
MAIN_MENU, CHAT_MODE, DIAGNOSIS_MODE, EMOTIONAL_SUPPORT, HEALTH_LIBRARY = range(5)

class UltimateRagnosisAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.user_profiles: Dict[int, Dict] = {}
        self.conversation_memory: Dict[int, List] = {}
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.load_data()
        self.startup_time = datetime.now()
        self.total_queries = 0
        print("🎉 Ultimate RAGnosis AI initialized with advanced features!")

    def load_data(self):
        """Load user data from JSON files"""
        try:
            # Load user profiles
            profiles_file = self.data_dir / "user_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    self.user_profiles = json.load(f)
            
            # Load conversation memory
            memory_file = self.data_dir / "conversation_memory.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                    self.conversation_memory = {int(k): v for k, v in memory_data.items()}
                    
        except Exception as e:
            print(f"⚠️ Could not load existing data: {e}")
            self.user_profiles = {}
            self.conversation_memory = {}

    def save_data(self):
        """Save user data to JSON files"""
        try:
            # Save user profiles
            profiles_file = self.data_dir / "user_profiles.json"
            with open(profiles_file, 'w') as f:
                json.dump(self.user_profiles, f, indent=2)
            
            # Save conversation memory
            memory_file = self.data_dir / "conversation_memory.json"
            with open(memory_file, 'w') as f:
                json.dump(self.conversation_memory, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save data: {e}")

    def search_wikipedia_medical(self, query: str, max_results: int = 3):
        """Search Wikipedia for medical information"""
        try:
            search_results = []
            
            medical_terms = [
                query,
                f"{query} (medicine)",
                f"{query} disease",
                f"{query} symptoms",
                f"{query} treatment",
                f"{query} diagnosis"
            ]
            
            for term in medical_terms:
                if len(search_results) >= max_results:
                    break
                    
                page = wiki_wiki.page(term)
                if page.exists() and len(page.summary) > 100:
                    preview = page.summary[:300] + "..." if len(page.summary) > 300 else page.summary
                    search_results.append({
                        "title": page.title,
                        "url": page.fullurl,
                        "preview": preview,
                        "full_summary": page.summary[:800]
                    })
            
            return search_results[:max_results]
            
        except Exception as e:
            print(f"❌ Wikipedia search error: {e}")
            return []

    def save_conversation(self, user_id: int, user_message: str, ai_response: str, conv_type: str = "general"):
        """Save conversation to memory"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        self.conversation_memory[user_id].append({
            "user": user_message,
            "ai": ai_response,
            "timestamp": datetime.now().isoformat(),
            "type": conv_type
        })
        
        # Keep only last 50 messages per user
        if len(self.conversation_memory[user_id]) > 50:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-50:]
        
        # Auto-save periodically
        if len(self.conversation_memory[user_id]) % 5 == 0:
            self.save_data()

    def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's conversation history"""
        if user_id not in self.conversation_memory:
            return []
        
        history = self.conversation_memory[user_id][-limit:]
        return history

    async def get_intelligent_response(self, user_id: int, user_message: str, context: str = "general") -> str:
        """Get intelligent, context-aware response with memory and Wikipedia"""
        
        start_time = time.time()
        self.total_queries += 1
        
        # Get conversation history
        history = self.get_conversation_history(user_id, 8)
        history_text = ""
        
        if history:
            history_text = "Previous conversation:\n"
            for i, msg in enumerate(history):
                history_text += f"User: {msg['user']}\nAI: {msg['ai']}\n\n"
        
        # Search Wikipedia for medical information
        wikipedia_results = []
        if any(keyword in user_message.lower() for keyword in 
               ['disease', 'symptom', 'treatment', 'medical', 'health', 'diagnosis', 'medicine', 'pain', 'illness', 'condition']):
            wikipedia_results = self.search_wikipedia_medical(user_message)
        
        # Build Wikipedia context
        wiki_context = ""
        if wikipedia_results:
            wiki_context = "\n\n📚 RELEVANT MEDICAL INFORMATION FROM WIKIPEDIA:\n"
            for i, result in enumerate(wikipedia_results, 1):
                wiki_context += f"{i}. {result['title']}: {result['preview']}\n"
        
        # Get user profile
        profile = self.user_profiles.get(user_id, {})
        profile_text = f"""
        User Profile:
        - Name: {profile.get('name', 'Friend')}
        - Conversation Count: {profile.get('conversation_count', 0)}
        - Health Interests: {profile.get('health_interests', 'General wellness')}
        """
        
        # Enhanced prompt for intelligent conversation
        prompt = f"""
        You are Ragnosis AI - an intelligent, empathetic, and highly capable medical AI assistant. 
        You're having a natural, flowing conversation with a user about their health concerns.

        USER PROFILE:
        {profile_text}

        CONVERSATION HISTORY (most recent first):
        {history_text}

        {wiki_context}

        CURRENT USER MESSAGE:
        "{user_message}"

        CONTEXT: {context}

        RESPONSE GUIDELINES:
        1. 🎯 Be NATURAL and CONVERSATIONAL - like a caring doctor friend
        2. 💡 Show genuine INTEREST and EMPATHY
        3. 🧠 Provide INSIGHTFUL medical perspective when relevant
        4. ❓ Ask thoughtful FOLLOW-UP questions to understand better
        5. 🌟 Use APPROPRIATE emojis to enhance communication
        6. 📚 Cite Wikipedia information when relevant
        7. 🔄 Reference previous conversation naturally
        8. 💪 EMPOWER and ENCOURAGE the user
        9. 🏥 Always include medical disclaimer for serious topics
        10. 🎨 Be CREATIVE in health discussions

        MEDICAL DISCLAIMER (include when discussing symptoms/treatments):
        "💡 Remember: I'm an AI assistant for informational purposes. Always consult healthcare professionals for medical advice."

        CONVERSATION FLOW:
        - Acknowledge their message naturally
        - Provide value (insight, information, or emotional support)
        - Ask a relevant follow-up question
        - Keep the conversation flowing naturally

        Response length: 4-7 sentences. Be engaging but concise.
        """

        try:
            response = gemini_model.generate_content(prompt)
            ai_response = response.text.strip()
            
            # Save to memory
            self.save_conversation(user_id, user_message, ai_response, context)
            
            response_time = time.time() - start_time
            print(f"✅ AI response generated in {response_time:.2f}s for user {user_id}")
            
            return ai_response
            
        except Exception as e:
            print(f"AI Response Error: {e}")
            return "🤖 I'm here and listening! Tell me more about how you're feeling today. 💬"

    def get_follow_up_questions(self, user_message: str) -> List[str]:
        """Generate relevant follow-up questions"""
        question_lower = user_message.lower()
        
        if any(word in question_lower for word in ['symptom', 'feel', 'pain', 'hurt', 'ache']):
            return [
                "How long have you been experiencing this?",
                "Have you noticed any triggers?",
                "What makes it better or worse?"
            ]
        elif any(word in question_lower for word in ['diagnos', 'test', 'result']):
            return [
                "Have you consulted a doctor about this?",
                "What tests have you had so far?",
                "When did you first notice these symptoms?"
            ]
        elif any(word in question_lower for word in ['treat', 'medic', 'therapy']):
            return [
                "What treatments have you tried?",
                "Are you currently taking any medications?",
                "Have you had any side effects?"
            ]
        else:
            return [
                "Would you like me to explain anything in more detail?",
                "Is there anything else you'd like to know?",
                "How are you feeling about this information?"
            ]

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with user profiling"""
        user = update.effective_user
        user_id = user.id
        
        # Initialize or update user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'name': user.first_name,
                'username': user.username,
                'join_date': datetime.now().isoformat(),
                'conversation_count': 0,
                'last_active': datetime.now().isoformat(),
                'health_interests': []
            }
        else:
            self.user_profiles[user_id]['last_active'] = datetime.now().isoformat()

        welcome_text = f"""
🤖 **Ragnosis AI - Ultimate Medical Companion** 🎉

👋 Hello {user.first_name}! I'm your advanced AI health assistant with:

✨ **Advanced Features:**
• 🧠 **Intelligent Chat** - Remembers our conversations
• 🔍 **Medical Research** - Wikipedia integration
• 💭 **Emotional Support** - Mental wellness guidance
• 📚 **Health Library** - Evidence-based information
• 🎯 **Symptom Analysis** - Detailed assessment
• 💊 **Treatment Info** - Medication insights
• 🌟 **Wellness Coaching** - Lifestyle guidance

💡 **I can help with:**
- Medical questions and information
- Symptom analysis and guidance  
- Emotional support and mental health
- Medication and treatment information
- Wellness and prevention tips
- Health education

**Choose your interaction mode below:** 👇
        """
        
        keyboard = [
            [KeyboardButton("🧠 Smart Chat"), KeyboardButton("🔍 Symptom Checker")],
            [KeyboardButton("💭 Emotional Support"), KeyboardButton("📚 Health Library")],
            [KeyboardButton("💊 Medication Info"), KeyboardButton("🌟 Wellness Coach")],
            [KeyboardButton("📊 Health Report"), KeyboardButton("ℹ️ Bot Info")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        self.save_data()
        return MAIN_MENU

    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu selections"""
        user_id = update.effective_user.id
        text = update.message.text
        
        menu_handlers = {
            "🧠 Smart Chat": self.start_smart_chat,
            "🔍 Symptom Checker": self.start_symptom_checker,
            "💭 Emotional Support": self.start_emotional_support,
            "📚 Health Library": self.start_health_library,
            "💊 Medication Info": self.start_medication_info,
            "🌟 Wellness Coach": self.start_wellness_coach,
            "📊 Health Report": self.generate_health_report,
            "ℹ️ Bot Info": self.show_bot_info
        }
        
        if text in menu_handlers:
            return await menu_handlers[text](update, context)
        else:
            # If user sends random text, start smart chat
            await update.message.reply_text(
                "💬 I see you want to chat! Let me switch to **Smart Chat Mode** for our conversation. 🧠",
                parse_mode='Markdown'
            )
            return await self.start_smart_chat(update, context)

    async def start_smart_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start intelligent chat mode"""
        user_id = update.effective_user.id
        
        # Update user profile
        self.user_profiles[user_id]['conversation_count'] += 1
        self.user_profiles[user_id]['last_active'] = datetime.now().isoformat()
        
        history = self.get_conversation_history(user_id, 5)
        
        welcome_msg = """
🧠 **Smart Chat Mode Activated!** 💫

I'm now in intelligent conversation mode! I'll:

• Remember our previous chats
• Provide medically accurate information  
• Search Wikipedia when needed
• Offer emotional support
• Ask relevant follow-up questions

**Just start talking!** Tell me about:
- Any health concerns
- Symptoms you're experiencing
- Medical questions
- How you're feeling
- Or anything health-related!

I'm here to listen and help! 💬
        """
        
        if history:
            welcome_msg += "\n\n📝 **I remember our previous conversation** - let's continue!"
        
        keyboard = [
            [KeyboardButton("🔍 Analyze Symptoms"), KeyboardButton("💊 Medication Query")],
            [KeyboardButton("📚 Research Topic"), KeyboardButton("💭 Emotional Check")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🔄 New Topic")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_MODE

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle intelligent chat conversations"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        print(f"💭 User {user_id}: {user_message}")
        
        # Handle quick actions
        if user_message == "🏠 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return MAIN_MENU
            
        elif user_message == "🔍 Analyze Symptoms":
            await update.message.reply_text(
                "🔍 **Symptom Analysis Mode**\n\nPlease describe your symptoms in detail...",
                parse_mode='Markdown'
            )
            return CHAT_MODE
            
        elif user_message == "💊 Medication Query":
            await update.message.reply_text(
                "💊 **Medication Information**\n\nWhat medication would you like to know about?",
                parse_mode='Markdown'
            )
            return CHAT_MODE
            
        elif user_message == "📚 Research Topic":
            await update.message.reply_text(
                "📚 **Health Research**\n\nWhat health topic would you like me to research?",
                parse_mode='Markdown'
            )
            return CHAT_MODE
            
        elif user_message == "💭 Emotional Check":
            await update.message.reply_text(
                "💭 **Emotional Check-in**\n\nHow are you feeling emotionally today?",
                parse_mode='Markdown'
            )
            return CHAT_MODE
            
        elif user_message == "🔄 New Topic":
            await update.message.reply_text(
                "🔄 **New Topic**\n\nWhat would you like to discuss now?",
                parse_mode='Markdown'
            )
            return CHAT_MODE
        
        # Show typing action
        await update.message.reply_chat_action("typing")
        
        # Get intelligent AI response
        ai_response = await self.get_intelligent_response(user_id, user_message, "smart_chat")
        
        # Get follow-up questions
        follow_ups = self.get_follow_up_questions(user_message)
        
        # Create response with follow-up options
        response_text = f"{ai_response}\n\n"
        
        if follow_ups:
            response_text += "💭 **Follow-up Questions:**\n"
            for i, question in enumerate(follow_ups[:2], 1):
                response_text += f"{i}. {question}\n"
        
        # Enhanced keyboard
        keyboard = [
            [KeyboardButton("🔍 More Details"), KeyboardButton("💭 Related Questions")],
            [KeyboardButton("📚 Research More"), KeyboardButton("💊 Medication Info")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🔄 New Topic")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_MODE

    async def start_symptom_checker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start advanced symptom analysis"""
        user_id = update.effective_user.id
        
        analysis_intro = """
🔍 **Advanced Symptom Checker** 🩺

I'll help you understand your symptoms better. Please describe:

• What you're experiencing
• When it started
• How severe it is (1-10 scale)
• Any patterns or triggers
• Other associated symptoms

**Please describe your main concern:** 👇
        """
        
        keyboard = [
            [KeyboardButton("🤒 Pain/Discomfort"), KeyboardButton("😴 Fatigue/Sleep Issues")],
            [KeyboardButton("🍎 Digestive Problems"), KeyboardButton("💓 Heart/Breathing")],
            [KeyboardButton("🧠 Mental/Emotional"), KeyboardButton("🌡️ Fever/Infection")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🧠 Switch to Chat")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(analysis_intro, reply_markup=reply_markup, parse_mode='Markdown')
        return DIAGNOSIS_MODE

    async def handle_diagnosis_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symptom analysis conversations"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🏠 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return MAIN_MENU
            
        elif user_message == "🧠 Switch to Chat":
            await self.start_smart_chat(update, context)
            return CHAT_MODE
        
        # Show typing action
        await update.message.reply_chat_action("typing")
        
        # Get detailed diagnostic response
        diagnostic_response = await self.get_intelligent_response(user_id, user_message, "symptom_analysis")
        
        # Enhanced diagnostic keyboard
        keyboard = [
            [KeyboardButton("📊 Severity Scale"), KeyboardButton("⏰ Duration/Timing")],
            [KeyboardButton("🔄 Related Symptoms"), KeyboardButton("💡 Possible Causes")],
            [KeyboardButton("🎯 Action Plan"), KeyboardButton("🏥 When to See Doctor")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🧠 General Chat")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(diagnostic_response, reply_markup=reply_markup, parse_mode='Markdown')
        return DIAGNOSIS_MODE

    async def start_emotional_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start emotional support mode"""
        user_id = update.effective_user.id
        
        emotional_welcome = """
💭 **Emotional Support Mode** 🌈

You're in a safe, confidential space. I'm here to:

• Listen without judgment
• Provide emotional support
• Offer coping strategies
• Help with stress management
• Guide mindfulness exercises

**What's on your mind today?** 💬
        """
        
        keyboard = [
            [KeyboardButton("😔 Stress/Anxiety"), KeyboardButton("😴 Sleep Issues")],
            [KeyboardButton("🎯 Mood Management"), KeyboardButton("🌈 Positive Mindset")],
            [KeyboardButton("🧘 Relaxation Tips"), KeyboardButton("📝 Journal Prompts")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🧠 Switch to Chat")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(emotional_welcome, reply_markup=reply_markup, parse_mode='Markdown')
        return EMOTIONAL_SUPPORT

    async def handle_emotional_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emotional support conversations"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🏠 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return MAIN_MENU
            
        elif user_message == "🧠 Switch to Chat":
            await self.start_smart_chat(update, context)
            return CHAT_MODE
        
        await update.message.reply_chat_action("typing")
        response = await self.get_intelligent_response(user_id, user_message, "emotional_support")
        
        keyboard = [
            [KeyboardButton("🌬️ Breathing Exercise"), KeyboardButton("📝 Journal Prompt")],
            [KeyboardButton("🎯 Coping Strategy"), KeyboardButton("🌈 Positive Affirmation")],
            [KeyboardButton("😊 Mood Booster"), KeyboardButton("💤 Sleep Help")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("💭 Continue Sharing")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
        return EMOTIONAL_SUPPORT

    async def start_health_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start health library mode"""
        user_id = update.effective_user.id
        
        library_intro = """
📚 **Health Knowledge Library** 🏥

I can provide evidence-based information on:

• Diseases & Conditions
• Symptoms & Diagnosis
• Treatments & Medications
• Prevention & Wellness
• Mental Health Topics
• Nutrition & Exercise

**What would you like to learn about?** 🔍
        """
        
        keyboard = [
            [KeyboardButton("🦠 Common Illnesses"), KeyboardButton("💊 Medications")],
            [KeyboardButton("🧠 Mental Health"), KeyboardButton("🍎 Nutrition")],
            [KeyboardButton("🏃‍♂️ Exercise"), KeyboardButton("🛌 Sleep Health")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("🧠 Switch to Chat")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(library_intro, reply_markup=reply_markup, parse_mode='Markdown')
        return HEALTH_LIBRARY

    async def handle_health_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle health library queries"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🏠 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return MAIN_MENU
            
        elif user_message == "🧠 Switch to Chat":
            await self.start_smart_chat(update, context)
            return CHAT_MODE
        
        await update.message.reply_chat_action("typing")
        response = await self.get_intelligent_response(user_id, user_message, "health_library")
        
        keyboard = [
            [KeyboardButton("🔍 More Details"), KeyboardButton("📖 Related Topics")],
            [KeyboardButton("💊 Treatment Info"), KeyboardButton("🎯 Prevention Tips")],
            [KeyboardButton("🏠 Main Menu"), KeyboardButton("📚 New Topic")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
        return HEALTH_LIBRARY

    async def start_medication_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start medication information mode"""
        await update.message.reply_text(
            "💊 **Medication Information**\n\nWhat medication would you like to know about?\n\n"
            "You can ask about:\n• Uses and indications\n• Side effects\n• Dosage information\n• Interactions\n• Precautions",
            parse_mode='Markdown'
        )
        return await self.start_smart_chat(update, context)

    async def start_wellness_coach(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start wellness coaching mode"""
        await update.message.reply_text(
            "🌟 **Wellness Coach Mode** 💪\n\nLet's work on your overall health and wellness!\n\n"
            "I can help with:\n• Nutrition guidance\n• Exercise planning\n• Stress management\n• Sleep optimization\n• Habit building\n• Goal setting",
            parse_mode='Markdown'
        )
        return await self.start_smart_chat(update, context)

    async def generate_health_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate comprehensive health report"""
        user_id = update.effective_user.id
        history = self.get_conversation_history(user_id, 20)
        
        if len(history) < 3:
            await update.message.reply_text(
                "📊 **Let's build your health profile first!**\n\n"
                "Chat with me a bit more in **Smart Chat Mode** so I can create "
                "a truly personalized health report for you! 🎯",
                parse_mode='Markdown'
            )
            return MAIN_MENU
        
        await update.message.reply_chat_action("typing")
        
        # Generate comprehensive report
        conversation_text = "\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in history])
        
        report_prompt = f"""
        Create a COMPREHENSIVE PERSONALIZED HEALTH REPORT based on this conversation history:

        {conversation_text}

        Create an ULTIMATE HEALTH REPORT with these sections:

        🎯 **Health Summary** (2-3 sentence overview)
        🔍 **Key Observations** (patterns and trends noticed)
        💡 **Important Insights** (significant health observations)
        🚀 **Growth Opportunities** (areas for improvement)
        🌟 **Health Strengths** (what they're doing well)
        📋 **Actionable Steps** (specific recommendations)
        🏆 **Wellness Goals** (suggested health goals)
        💝 **Encouragement & Support** (motivational message)

        Tone: Warm, professional, empowering. Use emojis naturally. 400-500 words.
        Be specific and reference actual conversation content when possible.
        """
        
        try:
            response = gemini_model.generate_content(report_prompt)
            report = response.text.strip()
            
            await update.message.reply_text(
                f"📊 **Your Comprehensive Health Report** 🎉\n\n{report}",
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text(
                "📊 **Your Health Snapshot** 🌟\n\n"
                "Based on our conversations, you're taking proactive steps toward better health! "
                "Keep up the great work of being engaged with your wellbeing. "
                "The more we communicate, the more personalized my insights become! 💪",
                parse_mode='Markdown'
            )
        
        return MAIN_MENU

    async def show_bot_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot information and statistics"""
        user_id = update.effective_user.id
        user_profile = self.user_profiles.get(user_id, {})
        
        info_text = f"""
🤖 **Ragnosis AI - System Information** 📊

**Your Profile:**
👤 Name: {user_profile.get('name', 'Friend')}
📅 Member Since: {user_profile.get('join_date', 'Recently')}
💬 Conversations: {user_profile.get('conversation_count', 0)}

**System Status:**
🕒 Uptime: {str(datetime.now() - self.startup_time).split('.')[0]}
📈 Total Queries: {self.total_queries}
👥 Active Users: {len(self.user_profiles)}
💾 Memory: {sum(len(conv) for conv in self.conversation_memory.values())} messages

**Features:**
• Intelligent conversation memory
• Wikipedia medical research
• Emotional support system
• Symptom analysis
• Health education library
• Wellness coaching

**Medical Disclaimer:**
💡 I'm an AI assistant for informational purposes. Always consult healthcare professionals for medical advice.
        """
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
        return MAIN_MENU

    async def return_to_main_menu(self, update: Update, user_id: int):
        """Return to main menu"""
        menu_text = """
🏠 **Main Menu** 🎯

Choose how you'd like to interact:

🧠 **Smart Chat** - General health conversations
🔍 **Symptom Checker** - Detailed symptom analysis  
💭 **Emotional Support** - Mental wellness guidance
📚 **Health Library** - Medical information
💊 **Medication Info** - Drug information
🌟 **Wellness Coach** - Lifestyle guidance
📊 **Health Report** - Personalized insights

**Select an option below:** 👇
        """
        
        keyboard = [
            [KeyboardButton("🧠 Smart Chat"), KeyboardButton("🔍 Symptom Checker")],
            [KeyboardButton("💭 Emotional Support"), KeyboardButton("📚 Health Library")],
            [KeyboardButton("💊 Medication Info"), KeyboardButton("🌟 Wellness Coach")],
            [KeyboardButton("📊 Health Report"), KeyboardButton("ℹ️ Bot Info")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
        return MAIN_MENU

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fallback message handler"""
        await update.message.reply_text(
            "🤖 **Hello! I'm Ragnosis AI** 🧠\n\n"
            "I see you sent a message. Let me guide you to the main menu where you can choose how you'd like to interact!",
            parse_mode='Markdown'
        )
        return await self.start_command(update, context)

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel any conversation and return to main menu"""
        user_id = update.effective_user.id
        await self.return_to_main_menu(update, user_id)
        return MAIN_MENU

def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully"""
    error = context.error
    
    if isinstance(error, Conflict):
        print("❌ BOT CONFLICT: Another instance is running. Stopping this instance...")
        # This will stop the conflicting instance
        raise SystemExit("Stopping due to bot conflict - only one instance should run")
    
    elif isinstance(error, NetworkError):
        print(f"🌐 Network error: {error}. Retrying...")
        
    else:
        print(f"⚠️ Unexpected error: {error}")

async def post_init(application: Application):
    """Run after bot is initialized"""
    print("🤖 Bot initialized successfully!")
    print("🔧 Setting up webhook...")
    
    # Clear any existing webhooks to prevent conflicts
    await application.bot.delete_webhook()
    print("✅ Webhook cleared - using polling mode")

def main():
    """Launch the ultimate RAGnosis AI"""
    print("🚀 LAUNCHING ULTIMATE RAGNOSIS AI...")
    print("🎊 Features: Memory + Wikipedia + Emotional Support + Advanced Diagnosis!")
    
    ragnosis_ai = UltimateRagnosisAI()
    
    # Create application with better configuration
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # ULTIMATE Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", ragnosis_ai.start_command),
            CommandHandler("menu", ragnosis_ai.return_to_main_menu),
            MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_message)
        ],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_main_menu)
            ],
            CHAT_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_chat_message)
            ],
            DIAGNOSIS_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_diagnosis_message)
            ],
            EMOTIONAL_SUPPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_emotional_support)
            ],
            HEALTH_LIBRARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_health_library)
            ]
        },
        fallbacks=[
            CommandHandler("start", ragnosis_ai.start_command),
            CommandHandler("cancel", ragnosis_ai.cancel_conversation),
            CommandHandler("menu", ragnosis_ai.return_to_main_menu),
            MessageHandler(filters.Regex('^🏠 Main Menu$'), ragnosis_ai.cancel_conversation),
            MessageHandler(filters.Regex('^/menu$'), ragnosis_ai.cancel_conversation)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True
    )
    
    # Add conversation handler
    application.add_handler(conv_handler)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(CommandHandler("info", ragnosis_ai.show_bot_info))
    application.add_handler(CommandHandler("report", ragnosis_ai.generate_health_report))
    
    print("✅ ULTIMATE RAGNOSIS AI READY!")
    print("🤖 Bot is now running with advanced features...")
    
    try:
        # Use polling with cleanup
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
    except Conflict as e:
        print("❌ CRITICAL: Bot conflict detected. Please ensure only one instance is running.")
        print("💡 Solution: Stop all other bot instances and restart this one.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        print("🔧 Bot stopped. Cleanup completed.")

if __name__ == '__main__':
    main()
