#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Ultimate Medical Companion
Fully-featured medical AI with intelligent chat, memory, and advanced diagnostics
"""

import os
import asyncio
import random
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
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

# Conversation states
CHAT_MODE, DIAGNOSIS_MODE, SYMPTOM_ANALYSIS, EMOTIONAL_SUPPORT = range(4)

class EnhancedRagnosisAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.user_profiles: Dict[int, Dict] = {}
        self.conversation_memory: Dict[int, List] = {}
        self.setup_database()
        print("🎉 Enhanced RAGnosis AI initialized with memory and intelligence!")

    def setup_database(self):
        """Setup SQLite database for persistent storage"""
        self.conn = sqlite3.connect('ragnosis_memory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_conversations (
                user_id INTEGER,
                timestamp TEXT,
                user_message TEXT,
                ai_response TEXT,
                conversation_type TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                medical_history TEXT,
                lifestyle TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        self.conn.commit()

    def save_conversation(self, user_id: int, user_message: str, ai_response: str, conv_type: str = "general"):
        """Save conversation to database"""
        self.cursor.execute('''
            INSERT INTO user_conversations (user_id, timestamp, user_message, ai_response, conversation_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, datetime.now().isoformat(), user_message, ai_response, conv_type))
        self.conn.commit()

    def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's conversation history"""
        self.cursor.execute('''
            SELECT user_message, ai_response, timestamp 
            FROM user_conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = self.cursor.fetchall()
        return [{"user": row[0], "ai": row[1], "timestamp": row[2]} for row in reversed(rows)]

    # 🧠 ENHANCED PERSONALITY SYSTEM
    PERSONALITY_TRAITS = {
        "warm": ["😊", "🤗", "💫", "🌟", "🌈"],
        "professional": ["🔍", "🎯", "📊", "🩺", "💡"],
        "encouraging": ["🚀", "💪", "🏆", "🎉", "✨"],
        "empathetic": ["❤️", "🤝", "🌷", "💝", "🌻"]
    }

    def get_personality_greeting(self) -> str:
        traits = random.choice(list(self.PERSONALITY_TRAITS.values()))
        emoji = random.choice(traits)
        greetings = [
            f"{emoji} Hey there! Dr. AI here, ready to chat about your health!",
            f"{emoji} Hello! Your friendly medical AI is online and listening!",
            f"{emoji} Hi! I'm here to help you feel better and understand your health!",
            f"{emoji} Welcome back! Ready to continue our health conversation?",
            f"{emoji} Greetings! Your personalized health companion is here!"
        ]
        return random.choice(greetings)

    async def get_intelligent_response(self, user_id: int, user_message: str, context: str = "general") -> str:
        """Get intelligent, context-aware response with memory"""
        
        # Get conversation history
        history = self.get_conversation_history(user_id, 8)
        history_text = ""
        
        if history:
            history_text = "Previous conversation:\n"
            for i, msg in enumerate(history):
                history_text += f"User: {msg['user']}\nAI: {msg['ai']}\n\n"
        
        # Get user profile
        profile = self.user_profiles.get(user_id, {})
        profile_text = f"""
        User Profile:
        - Name: {profile.get('name', 'Friend')}
        - Age: {profile.get('age', 'Not specified')}
        - Gender: {profile.get('gender', 'Not specified')}
        - Health Interests: {profile.get('health_interests', 'General wellness')}
        """
        
        # Enhanced prompt for intelligent conversation
        prompt = f"""
        You are RAGnosis AI - an intelligent, empathetic, and highly capable medical AI assistant. 
        You're having a natural, flowing conversation with a user about their health concerns.

        USER PROFILE:
        {profile_text}

        CONVERSATION HISTORY (most recent first):
        {history_text}

        CURRENT USER MESSAGE:
        "{user_message}"

        CONTEXT: {context}

        RESPONSE GUIDELINES:
        1. 🎯 Be NATURAL and CONVERSATIONAL - like a caring doctor friend
        2. 💡 Show genuine INTEREST and EMPATHY
        3. 🧠 Provide INSIGHTFUL medical perspective when relevant
        4. ❓ Ask thoughtful FOLLOW-UP questions to understand better
        5. 🌟 Use APPROPRIATE emojis to enhance communication
        6. 📚 Cite reliable medical information when applicable
        7. 🔄 Reference previous conversation naturally when relevant
        8. 💪 EMPOWER and ENCOURAGE the user
        9. 🎨 Be CREATIVE in your approach to health discussions
        10. 🏥 Always emphasize PROFESSIONAL medical advice for serious concerns

        CONVERSATION FLOW:
        - Acknowledge their message naturally
        - Provide value (insight, information, or emotional support)
        - Ask a relevant follow-up question
        - Keep the conversation flowing naturally

        Response length: 3-6 sentences. Be engaging but concise.
        """

        try:
            response = gemini_model.generate_content(prompt)
            ai_response = response.text.strip()
            
            # Save to memory
            self.save_conversation(user_id, user_message, ai_response, context)
            
            return ai_response
            
        except Exception as e:
            print(f"AI Response Error: {e}")
            return "🤖 I'm here and listening! Tell me more about how you're feeling today. 💬"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start with intelligent memory"""
        user = update.effective_user
        user_id = user.id
        
        # Initialize or update user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'name': user.first_name,
                'join_date': datetime.now().strftime("%Y-%m-%d"),
                'conversation_count': 0,
                'last_active': datetime.now(),
                'health_interests': []
            }
        else:
            self.user_profiles[user_id]['last_active'] = datetime.now()

        welcome_text = f"""
{self.get_personality_greeting()}

**I'm RAGnosis AI 2.0** - Your Intelligent Health Companion! 🧠

🎊 **Enhanced Features:**
• 🧠 **Smart Chat** - Remembers our conversations and learns about you
• 🎯 **Advanced Diagnosis** - Deep symptom analysis with follow-up questions  
• 💭 **Emotional Intelligence** - Understands your feelings and mood
• 📚 **Medical Knowledge** - Evidence-based health information
• 🏋️ **Personalized Advice** - Tailored to your unique situation
• 🔄 **Continuous Learning** - Gets better the more we talk
• 🎨 **Creative Health Solutions** - Fun and innovative approaches

**Choose how you'd like to interact today:** 🚀
        """
        
        keyboard = [
            [KeyboardButton("🧠 Smart Chat Mode"), KeyboardButton("🎯 Advanced Diagnosis")],
            [KeyboardButton("💭 Emotional Support"), KeyboardButton("🏋️ Wellness Coach")],
            [KeyboardButton("📚 Health Library"), KeyboardButton("🔍 Symptom Checker")],
            [KeyboardButton("📊 Health Report"), KeyboardButton("🎮 Health Games")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def start_smart_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start intelligent chat mode with memory"""
        user_id = update.effective_user.id
        
        # Get recent conversation history
        history = self.get_conversation_history(user_id, 5)
        
        welcome_msg = f"""
🧠 **Smart Chat Mode Activated!** 🎉

{self.get_personality_greeting()}

I remember our previous conversations and I'm here to continue supporting your health journey!

💫 **What makes this special:**
• I remember what we've discussed
• I learn about your health patterns
• I provide personalized insights
• Our conversation flows naturally

**Just start talking!** Tell me about:
• How you're feeling today
• Any health concerns
• Your wellness goals
• Or anything health-related!

I'm listening carefully and will respond thoughtfully. 💬
        """
        
        if history:
            welcome_msg += "\n\n📝 **I recall our previous chat** - let's continue where we left off!"
        
        keyboard = [
            [KeyboardButton("🔍 Analyze Symptoms"), KeyboardButton("💭 How are you feeling?")],
            [KeyboardButton("🏋️ Wellness Check"), KeyboardButton("📊 Generate Insight")],
            [KeyboardButton("🔄 Change Mode"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_MODE

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle intelligent chat with memory and context"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        print(f"💭 User {user_id}: {user_message}")
        
        # Handle quick actions
        quick_actions = {
            "🔍 Analyze Symptoms": "symptom_analysis",
            "💭 How are you feeling?": "emotional_check",
            "🏋️ Wellness Check": "wellness_check", 
            "📊 Generate Insight": "generate_insight",
            "🔄 Change Mode": "change_mode",
            "🏠 Main Menu": "main_menu"
        }
        
        if user_message in quick_actions:
            return await self.handle_quick_action(update, user_id, quick_actions[user_message])
        
        # Update user profile
        self.user_profiles[user_id]['conversation_count'] = self.user_profiles[user_id].get('conversation_count', 0) + 1
        self.user_profiles[user_id]['last_active'] = datetime.now()
        
        # Show typing indicator
        await update.message.reply_chat_action("typing")
        
        # Get intelligent response
        ai_response = await self.get_intelligent_response(user_id, user_message, "smart_chat")
        
        # Enhanced keyboard based on conversation context
        keyboard = [
            [KeyboardButton("🔍 Analyze Deeper"), KeyboardButton("💭 Tell me more")],
            [KeyboardButton("🏋️ Wellness Tips"), KeyboardButton("📊 Get Summary")],
            [KeyboardButton("🔄 New Topic"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(ai_response, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_MODE

    async def handle_quick_action(self, update: Update, user_id: int, action: str):
        """Handle quick action buttons"""
        
        if action == "main_menu":
            await self.return_to_main_menu(update, user_id)
            return ConversationHandler.END
            
        elif action == "symptom_analysis":
            await self.start_symptom_analysis(update, user_id)
            return DIAGNOSIS_MODE
            
        elif action == "emotional_check":
            response = await self.get_intelligent_response(user_id, "I want to talk about how I'm feeling emotionally", "emotional_support")
            await update.message.reply_text(response, parse_mode='Markdown')
            return CHAT_MODE
            
        elif action == "wellness_check":
            wellness_prompt = "Give me a wellness check and lifestyle assessment"
            response = await self.get_intelligent_response(user_id, wellness_prompt, "wellness_check")
            await update.message.reply_text(response, parse_mode='Markdown')
            return CHAT_MODE
            
        elif action == "generate_insight":
            await self.generate_health_insight(update, user_id)
            return CHAT_MODE
            
        elif action == "change_mode":
            await update.message.reply_text(
                "🔄 **Changing Modes**\n\nWhich mode would you prefer?",
                reply_markup=ReplyKeyboardMarkup([
                    ["🎯 Diagnosis Mode", "💭 Emotional Mode"],
                    ["🏋️ Wellness Mode", "🧠 Continue Smart Chat"],
                    ["🏠 Main Menu"]
                ], resize_keyboard=True)
            )
            return CHAT_MODE

    async def start_symptom_analysis(self, update: Update, user_id: int):
        """Start advanced symptom analysis"""
        
        analysis_intro = """
🔍 **Advanced Symptom Analysis** 🎯

I'm now in diagnosis mode! I'll ask thoughtful questions to understand your symptoms thoroughly.

💡 **My approach:**
- Deep understanding of your symptoms
- Context-aware questioning
- Personalized risk assessment
- Actionable recommendations

**Please describe your main symptom or health concern:** 🗣️

You can tell me:
- What you're experiencing
- When it started
- How severe it is
- Anything that makes it better or worse
        """
        
        keyboard = [
            [KeyboardButton("🤒 Pain/Discomfort"), KeyboardButton("😴 Fatigue/Sleep")],
            [KeyboardButton("🍎 Digestive Issues"), KeyboardButton("💓 Heart/Breathing")],
            [KeyboardButton("🧠 Mental/Emotional"), KeyboardButton("🔙 Back to Chat")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(analysis_intro, reply_markup=reply_markup, parse_mode='Markdown')
        return DIAGNOSIS_MODE

    async def handle_diagnosis_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symptom analysis conversations"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🔙 Back to Chat":
            await self.return_to_chat_mode(update, user_id)
            return CHAT_MODE
        
        # Get intelligent diagnostic response
        await update.message.reply_chat_action("typing")
        diagnostic_response = await self.get_intelligent_response(user_id, user_message, "symptom_analysis")
        
        # Diagnostic-specific keyboard
        keyboard = [
            [KeyboardButton("🔍 More Symptoms"), KeyboardButton("📊 Severity Level")],
            [KeyboardButton("⏰ Duration/Timing"), KeyboardButton("🔄 Related Symptoms")],
            [KeyboardButton("💡 Possible Causes"), KeyboardButton("🎯 Action Plan")],
            [KeyboardButton("🔙 Back to Chat"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(diagnostic_response, reply_markup=reply_markup, parse_mode='Markdown')
        return DIAGNOSIS_MODE

    async def generate_health_insight(self, update: Update, user_id: int):
        """Generate personalized health insights based on conversation history"""
        
        history = self.get_conversation_history(user_id, 15)
        if not history:
            await update.message.reply_text("💬 Let's chat a bit more so I can generate personalized insights for you!")
            return CHAT_MODE
        
        await update.message.reply_chat_action("typing")
        
        # Create insight prompt
        conversation_summary = "\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in history[-10:]])
        
        insight_prompt = f"""
        Based on this conversation history, generate DEEP PERSONALIZED HEALTH INSIGHTS:

        CONVERSATION HISTORY:
        {conversation_summary}

        USER PROFILE:
        {self.user_profiles.get(user_id, {})}

        Create a COMPREHENSIVE but CONVERSATIONAL insight report covering:

        🎯 **Patterns Noticed** (what I observe about their health)
        💡 **Key Insights** (important observations)
        🚀 **Growth Opportunities** (areas for improvement)
        🌟 **Strengths** (what they're doing well)
        🔮 **Future Focus** (what to pay attention to)
        💪 **Empowerment Message** (encouraging next steps)

        Format: Very conversational, like a caring health coach. Use emojis. 300-400 words.
        """
        
        try:
            response = gemini_model.generate_content(insight_prompt)
            insight = response.text.strip()
            
            await update.message.reply_text(
                f"📊 **Your Personalized Health Insight** 🎉\n\n{insight}",
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text(
                "💡 **What I'm Learning About You:**\n\n"
                "Based on our conversations, I see you're proactive about your health! "
                "Keep sharing your experiences - the more we talk, the better I can support your wellness journey! 🌟"
            )

    async def return_to_chat_mode(self, update: Update, user_id: int):
        """Return to smart chat mode"""
        await update.message.reply_text(
            "🧠 **Returning to Smart Chat Mode**\n\n"
            "I'm here and ready to continue our conversation! What would you like to talk about? 💬",
            reply_markup=ReplyKeyboardMarkup([
                ["🔍 Analyze Symptoms", "💭 How are you feeling?"],
                ["🏋️ Wellness Check", "📊 Generate Insight"],
                ["🔄 Change Mode", "🏠 Main Menu"]
            ], resize_keyboard=True)
        )
        return CHAT_MODE

    async def return_to_main_menu(self, update: Update, user_id: int):
        """Return to main menu"""
        await update.message.reply_text(
            "🏠 **Welcome back to Main Menu!**\n\n"
            "Where would you like to go next? 🎉",
            reply_markup=ReplyKeyboardMarkup([
                ["🧠 Smart Chat Mode", "🎯 Advanced Diagnosis"],
                ["💭 Emotional Support", "🏋️ Wellness Coach"],
                ["📚 Health Library", "🔍 Symptom Checker"],
                ["📊 Health Report", "🎮 Health Games"]
            ], resize_keyboard=True)
        )

    # Enhanced feature handlers
    async def start_emotional_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start emotional support mode"""
        user_id = update.effective_user.id
        
        emotional_welcome = """
💭 **Emotional Support Mode** 🌈

I'm here to listen, understand, and support you emotionally.

🤗 **What we can do together:**
- Talk about your feelings and stress
- Develop coping strategies
- Practice mindfulness techniques
- Build emotional resilience
- Create positive mental habits

**You're in a safe space. Tell me what's on your mind:** 💬
        """
        
        keyboard = [
            [KeyboardButton("😔 Stress/Anxiety"), KeyboardButton("😴 Sleep Issues")],
            [KeyboardButton("🎯 Mood Management"), KeyboardButton("🌈 Positive Mindset")],
            [KeyboardButton("🧘 Relaxation Tips"), KeyboardButton("🔙 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(emotional_welcome, reply_markup=reply_markup, parse_mode='Markdown')
        return EMOTIONAL_SUPPORT

    async def handle_emotional_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emotional support conversations"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_message == "🔙 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return ConversationHandler.END
        
        await update.message.reply_chat_action("typing")
        response = await self.get_intelligent_response(user_id, user_message, "emotional_support")
        
        keyboard = [
            [KeyboardButton("🌬️ Breathing Exercise"), KeyboardButton("📝 Journal Prompt")],
            [KeyboardButton("🎯 Coping Strategy"), KeyboardButton("🌈 Positive Affirmation")],
            [KeyboardButton("💭 Continue Sharing"), KeyboardButton("🔙 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
        return EMOTIONAL_SUPPORT

    async def handle_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Master message handler for main menu"""
        text = update.message.text
        
        feature_handlers = {
            "🧠 Smart Chat Mode": self.start_smart_chat,
            "🎯 Advanced Diagnosis": self.start_symptom_analysis,
            "💭 Emotional Support": self.start_emotional_support,
            "🏋️ Wellness Coach": self.start_wellness_coach,
            "📚 Health Library": self.show_health_library,
            "🔍 Symptom Checker": self.start_symptom_analysis,
            "📊 Health Report": self.generate_health_report,
            "🎮 Health Games": self.show_health_games,
            "🏠 Main Menu": self.return_to_main_menu
        }
        
        if text in feature_handlers:
            if text in ["🧠 Smart Chat Mode", "🎯 Advanced Diagnosis", "💭 Emotional Support"]:
                return await feature_handlers[text](update, context)
            else:
                await feature_handlers[text](update, context)
        else:
            # Suggest starting a conversation
            await update.message.reply_text(
                "🤖 **Hello! I'm RAGnosis AI** 🧠\n\n"
                "I'm your intelligent health companion with memory and understanding! "
                "Try **'🧠 Smart Chat Mode'** to start a conversation I'll remember, "
                "or choose any feature from the menu below! 🎉",
                reply_markup=ReplyKeyboardMarkup([
                    ["🧠 Smart Chat Mode", "🎯 Advanced Diagnosis"],
                    ["💭 Emotional Support", "🏋️ Wellness Coach"],
                    ["📚 Health Library", "🔍 Symptom Checker"]
                ], resize_keyboard=True)
            )

    # Additional feature implementations
    async def start_wellness_coach(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wellness coaching mode"""
        await update.message.reply_text(
            "🏋️ **Wellness Coach Mode** 💪\n\n"
            "Let's work on your overall wellness! I can help with:\n\n"
            "• 🍎 Nutrition guidance\n• 💤 Sleep optimization\n"
            "• 🏃‍♂️ Exercise planning\n• 😊 Stress management\n"
            "• 🌟 Habit building\n• 🎯 Goal setting\n\n"
            "What wellness area would you like to focus on today?",
            reply_markup=ReplyKeyboardMarkup([
                ["🍎 Nutrition", "💤 Sleep", "🏃‍♂️ Exercise"],
                ["😊 Stress Management", "🌟 Habit Building"],
                ["🔙 Main Menu"]
            ], resize_keyboard=True)
        )

    async def show_health_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Health information library"""
        await update.message.reply_text(
            "📚 **Health Knowledge Library** 🏥\n\n"
            "I can provide evidence-based information on:\n\n"
            "• Common conditions and treatments\n• Preventive healthcare\n"
            "• Mental health topics\n• Nutrition science\n"
            "• Fitness and exercise\n• Medication information\n\n"
            "**Just ask me anything health-related in chat mode!** 🗣️",
            reply_markup=ReplyKeyboardMarkup([
                ["🧠 Ask Health Question", "🔍 Research Symptom"],
                ["📖 Learn Prevention", "🎯 Treatment Options"],
                ["🔙 Main Menu"]
            ], resize_keyboard=True)
        )

    async def generate_health_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate comprehensive health report"""
        user_id = update.effective_user.id
        history = self.get_conversation_history(user_id, 20)
        
        if len(history) < 3:
            await update.message.reply_text(
                "📊 **Let's build your health profile!**\n\n"
                "Chat with me a bit more in **Smart Chat Mode** so I can create "
                "a truly personalized health report for you! 🎯"
            )
            return
        
        await update.message.reply_chat_action("typing")
        
        # Generate comprehensive report
        conversation_text = "\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in history])
        
        report_prompt = f"""
        Create a COMPREHENSIVE PERSONALIZED HEALTH REPORT based on this conversation history:

        {conversation_text}

        USER PROFILE: {self.user_profiles.get(user_id, {})}

        Create an ULTIMATE HEALTH REPORT with these sections:

        🎯 **Executive Summary** (2-3 sentence overview)
        🔍 **Health Patterns** (observed trends and patterns)
        💡 **Key Insights** (important health observations)
        🚀 **Opportunities** (areas for improvement)
        🌟 **Strengths** (what they're doing well)
        📋 **Action Plan** (specific, actionable steps)
        🏆 **Goals** (recommended health goals)
        💝 **Encouragement** (motivational message)

        Tone: Warm, professional, empowering. Use emojis naturally. 400-500 words.
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
                "The more we communicate, the more personalized my insights become! 💪"
            )

    async def show_health_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Health-related interactive activities"""
        games = [
            "🎮 **Health Trivia:** True or False: Regular exercise can improve sleep quality! 💤",
            "🤔 **Symptom Solver:** I'm thinking of a symptom that improves with rest... what could it be? 💭",
            "🏆 **Wellness Challenge:** Take 5 deep breaths right now! 🌬️",
            "🎯 **Health Quiz:** Which vitamin is known as the 'sunshine vitamin'? ☀️",
            "🌈 **Gratitude Game:** Name 3 things your body did well today! ✨"
        ]
        
        await update.message.reply_text(
            random.choice(games),
            reply_markup=ReplyKeyboardMarkup([
                ["🎮 Another Game", "📊 Health Fact"],
                ["🏋️ Wellness Challenge", "🔙 Main Menu"]
            ], resize_keyboard=True)
        )

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel any conversation"""
        user_id = update.effective_user.id
        await self.return_to_main_menu(update, user_id)
        return ConversationHandler.END

def main():
    """Launch the enhanced RAGnosis AI"""
    print("🚀 LAUNCHING ENHANCED RAGNOSIS AI...")
    print("🧠 Features: Memory + Intelligent Chat + Advanced Diagnosis + Emotional AI")
    
    ragnosis_ai = EnhancedRagnosisAI()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ENHANCED Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🧠 Smart Chat Mode$'), ragnosis_ai.start_smart_chat),
            MessageHandler(filters.Regex('^🎯 Advanced Diagnosis$'), ragnosis_ai.start_symptom_analysis),
            MessageHandler(filters.Regex('^💭 Emotional Support$'), ragnosis_ai.start_emotional_support)
        ],
        states={
            CHAT_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_chat_message)
            ],
            DIAGNOSIS_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_diagnosis_message)
            ],
            EMOTIONAL_SUPPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_emotional_support)
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex('^🏠 Main Menu$'), ragnosis_ai.cancel_conversation),
            MessageHandler(filters.Regex('^🔙 Main Menu$'), ragnosis_ai.cancel_conversation),
            MessageHandler(filters.Regex('^🔙 Back to Chat$'), ragnosis_ai.return_to_chat_mode),
            CommandHandler('cancel', ragnosis_ai.cancel_conversation)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True
    )
    
    # Add all handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_all_messages))
    
    print("✅ ENHANCED RAGNOSIS AI READY!")
    print("🎊 Features: Memory + Intelligent Responses + Advanced Analysis + Emotional Support!")
    print("🤖 Bot is now running with enhanced capabilities...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
