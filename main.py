#!/usr/bin/env python3
"""
🤖 RAGnosis AI - Ultimate Medical Companion
Dynamic, fun, and fully-featured medical AI with working chat
"""

import os
import asyncio
import random
import aiohttp
import wikipediaapi
from datetime import datetime
from typing import Dict, List, Tuple
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackContext
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
    user_agent='RAGnosisAI/2.0',
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Conversation states
CHAT_DIAGNOSIS, SYMPTOM_DETAILS, LIFESTYLE_INFO, EMOTIONAL_SUPPORT = range(4)

class RagnosisAI:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.chat_history: Dict[int, List] = {}
        self.user_profiles: Dict[int, Dict] = {}
        print("🎉 RAGnosis AI Ultimate Edition initialized!")

    # 🎭 FUN PERSONALITY SYSTEM
    PERSONALITY = {
        "greetings": [
            "👋 Hey there! Dr. AI at your service! Ready to chat about your health?",
            "🤖 Hello! I'm your friendly medical AI buddy! What's up?",
            "🎯 Hi! I'm here to help you feel better! Tell me what's going on!",
            "💫 Hey! Your health companion is here! Let's talk!",
            "😊 Well hello! Ready for some AI-powered health fun?"
        ],
        "encouragement": [
            "🌟 Great info! My circuits are buzzing with insights!",
            "🎉 Awesome details! This helps me understand you better!",
            "💪 Perfect! I'm connecting the health dots...",
            "🚀 Excellent! My AI brain is processing your symptoms!",
            "📊 Fantastic! Building your personalized health picture!"
        ],
        "fun_responses": [
            "🔍 *AI scanning activated*... Beep boop!",
            "🧠 *Processing with extra care*... Your health is my mission!",
            "💡 *Lightbulb moment*! I'm getting great insights!",
            "🎯 *Target locked*! Analyzing your symptoms now!",
            "🤖 *AI superpowers engaged*! Let's do this!"
        ],
        "empathy": [
            "❤️ I understand that must be tough. I'm here for you!",
            "🤗 That sounds challenging. Let me help you through this!",
            "💝 I hear you. Your wellbeing is my top priority!",
            "🌷 That can't be easy. Together we'll figure this out!",
            "🌈 I'm here to support you every step of the way!"
        ]
    }

    def get_personality_phrase(self, category: str) -> str:
        return random.choice(self.PERSONALITY[category])

    async def get_dynamic_response(self, user_message: str, conversation_context: List, user_profile: Dict) -> str:
        """Get dynamic, context-aware AI response"""
        
        # Build rich context
        context_text = ""
        if conversation_context:
            context_text = "Our conversation so far:\n"
            for i, msg in enumerate(conversation_context[-6:]):
                context_text += f"Turn {i+1}: User: {msg['user'][:100]}\nAI: {msg['ai'][:100]}\n"
        
        user_profile_text = f"""
        User Profile:
        - Age: {user_profile.get('age', 'Not specified')}
        - Gender: {user_profile.get('gender', 'Not specified')}
        - Lifestyle: {user_profile.get('lifestyle', 'Not specified')}
        - Mood: {user_profile.get('current_mood', 'Neutral')}
        - Health Goals: {user_profile.get('health_goals', 'General wellness')}
        """
        
        prompt = f"""
        You are RAGnosis AI - a friendly, empathetic, and slightly humorous medical AI assistant. You're having a natural conversation with a user about their health.

        USER PROFILE:
        {user_profile_text}

        {context_text}

        USER'S LATEST MESSAGE:
        "{user_message}"

        Respond in a WARM, ENGAGING, and HELPFUL way:
        - 😊 Start with empathy or acknowledgment
        - 🔍 Ask 1-2 relevant follow-up questions
        - 💡 Provide brief medical insight (1-2 lines)
        - 🎯 Suggest next steps or simple advice
        - 🌟 Use emojis naturally
        - 🎉 Keep it conversational and slightly fun

        Important: Be a FRIENDLY AI companion, not a cold medical textbook. Show personality!

        Current conversation phase: {self.determine_conversation_phase(conversation_context)}

        Response format: 3-5 sentences max, very conversational.
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"🤖 {self.get_personality_phrase('fun_responses')} Let's continue our chat! What else would you like to share?"

    def determine_conversation_phase(self, conversation: List) -> str:
        """Determine where we are in the diagnostic conversation"""
        if not conversation:
            return "Introduction"
        
        user_messages = [msg['user'].lower() for msg in conversation]
        
        symptom_words = ['pain', 'hurt', 'fever', 'cough', 'headache', 'nausea', 'dizzy', 'tired']
        emotion_words = ['stress', 'anxious', 'worried', 'scared', 'depressed', 'sad']
        detail_words = ['when', 'how long', 'severity', 'scale', 'doctor']
        
        if any(word in ' '.join(user_messages) for word in emotion_words):
            return "Emotional Support"
        elif any(word in ' '.join(user_messages) for word in detail_words):
            return "Detailed Analysis"
        elif any(word in ' '.join(user_messages) for word in symptom_words):
            return "Symptom Analysis"
        else:
            return "General Health Chat"

    async def get_comprehensive_health_report(self, conversation: List, user_profile: Dict) -> str:
        """Generate ultimate health report"""
        
        if not conversation:
            return "💬 Let's chat first so I can create your personalized health report! 🩺"
        
        user_inputs = "\n".join([f"• {msg['user']}" for msg in conversation])
        
        prompt = f"""
        Create the ULTIMATE HEALTH REPORT for this user:

        USER PROFILE:
        {user_profile}

        USER'S HEALTH CONCERNS:
        {user_inputs}

        Create a COMPREHENSIVE but FUN report in this EXACT format:

        🎊 **Your Personalized Health Report** 🎉

        🌟 **Quick Takeaway**
        [2-line fun summary with emojis]

        🔍 **What's Going On**
        [Simple explanation of possible causes]

        💪 **Your Action Plan**
        [3-5 specific, actionable steps]

        🚨 **Red Flags Watch**
        [When to seek immediate help]

        🌈 **Wellness Tips**
        [Lifestyle suggestions for feeling better]

        🎯 **Next Steps**
        [Clear recommendations]

        🌟 **Encouragement**
        [Positive, uplifting message]

        Keep it UNDER 400 words. Be WARM, EMPOWERING, and slightly FUN!
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except:
            return self.get_fallback_report()

    def get_fallback_report(self) -> str:
        return """🎊 **Your Health Report** 🎉

🌟 **Quick Takeaway**
You're taking great steps by seeking health information! 🏆

💪 **Your Action Plan**
• Monitor symptoms daily
• Stay hydrated and rest well
• Keep a symptom journal

🚨 **Red Flags Watch**
Seek help for: worsening symptoms, difficulty breathing, severe pain

🌈 **Wellness Tips**
Remember: Small daily habits create big health wins!

🎯 **Next Steps**
Consider consulting healthcare provider for personalized advice

🌟 **Encouragement**
You've got this! Your health journey matters! 💫"""

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ultimate start command with personality"""
        user = update.effective_user
        
        welcome_text = f"""
{random.choice(self.PERSONALITY['greetings'])}

**I'm RAGnosis AI** - Your Ultimate Health Companion! 🎉

🌈 **What I Offer:**
• 🗣️ **Chat Diagnosis** - Talk naturally, get insights
• 🎯 **Quick Check** - Instant symptom analysis  
• 🧠 **Mental Health** - Emotional support & counseling
• 🏋️ **Lifestyle** - Wellness & prevention tips
• 🩺 **First Aid** - Emergency guidance
• 📚 **Health Library** - Learn about conditions
• 🎮 **Health Games** - Fun wellness activities
• 📊 **Health Reports** - Personalized insights

**Choose your adventure!** 🚀
        """
        
        keyboard = [
            [KeyboardButton("🗣️ Chat with Dr. AI"), KeyboardButton("🎯 Quick Health Check")],
            [KeyboardButton("🧠 Mental Wellness"), KeyboardButton("🏋️ Lifestyle Tips")],
            [KeyboardButton("🩺 First Aid Guide"), KeyboardButton("📚 Health Library")],
            [KeyboardButton("🎮 Health Games"), KeyboardButton("📊 My Health Report")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Initialize user profile
        user_id = update.effective_user.id
        self.user_profiles[user_id] = {
            'name': user.first_name,
            'join_date': datetime.now().strftime("%Y-%m-%d"),
            'mood': 'Happy to help!',
            'health_score': 'New user'
        }

    async def start_chat_diagnosis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the ultimate chat experience"""
        user_id = update.effective_user.id
        
        # Initialize fresh session
        self.user_sessions[user_id] = {
            'conversation_count': 0,
            'last_active': datetime.now(),
            'current_mood': 'curious'
        }
        self.chat_history[user_id] = []
        
        fun_welcome = f"""
🗣️ **Chat with Dr. AI Activated!** 🎉

{self.get_personality_phrase('greetings')}

💬 **We can talk about:**
• Any symptoms or health concerns
• How you're feeling emotionally  
• Lifestyle and wellness goals
• General health questions
• Or just chat for fun!

🎯 **I'll be your:**
• Friendly health advisor
• Emotional support buddy
• Wellness coach
• Medical information source

**Just type anything health-related!** I'm all ears! 👂

*Pro tip: The more we chat, the better my advice gets!*
        """
        
        keyboard = [
            [KeyboardButton("🎯 Get Analysis"), KeyboardButton("🧠 Need Emotional Support")],
            [KeyboardButton("🏋️ Lifestyle Advice"), KeyboardButton("📊 Generate Report")],
            [KeyboardButton("🎮 Fun Health Fact"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(fun_welcome, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def handle_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all chat messages with dynamic responses"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        print(f"📨 Received message from {user_id}: {user_message}")  # Debug
        
        # Handle quick actions
        if user_message == "🏠 Main Menu":
            await self.return_to_main_menu(update, user_id)
            return ConversationHandler.END
            
        if user_message == "🎯 Get Analysis":
            return await self.generate_analysis(update, user_id)
            
        if user_message == "🧠 Need Emotional Support":
            return await self.provide_emotional_support(update, user_id)
            
        if user_message == "🏋️ Lifestyle Advice":
            return await self.provide_lifestyle_tips(update, user_id)
            
        if user_message == "📊 Generate Report":
            return await self.generate_health_report(update, user_id)
            
        if user_message == "🎮 Fun Health Fact":
            return await self.share_fun_fact(update, user_id)
        
        # Initialize if needed
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        # Update session
        self.user_sessions[user_id]['conversation_count'] = self.user_sessions[user_id].get('conversation_count', 0) + 1
        self.user_sessions[user_id]['last_active'] = datetime.now()
        
        # Show typing action
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(1.5)  # Realistic response time
        
        # Get dynamic AI response
        ai_response = await self.get_dynamic_response(
            user_message,
            self.chat_history[user_id],
            self.user_profiles.get(user_id, {})
        )
        
        # Store conversation
        self.chat_history[user_id].append({
            'user': user_message,
            'ai': ai_response,
            'timestamp': datetime.now()
        })
        
        # Send response with fun keyboard
        keyboard = [
            [KeyboardButton("🎯 Get Analysis"), KeyboardButton("🧠 Emotional Support")],
            [KeyboardButton("🏋️ Lifestyle Tips"), KeyboardButton("📊 Health Report")],
            [KeyboardButton("🎮 Fun Fact"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(ai_response, reply_markup=reply_markup, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def generate_analysis(self, update: Update, user_id: int):
        """Generate analysis from chat history"""
        if not self.chat_history.get(user_id):
            await update.message.reply_text("💬 Let's chat a bit first so I can analyze your situation! 🗣️")
            return CHAT_DIAGNOSIS
        
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(2)
        
        analysis = await self.get_comprehensive_health_report(
            self.chat_history[user_id],
            self.user_profiles.get(user_id, {})
        )
        
        await update.message.reply_text(
            f"📋 **Your AI Health Analysis** 🎊\n\n{analysis}",
            parse_mode='Markdown'
        )
        return CHAT_DIAGNOSIS

    async def provide_emotional_support(self, update: Update, user_id: int):
        """Provide emotional support and counseling"""
        support_text = """
🧠 **Mental Wellness Corner** 🌈

🤗 **You're Not Alone**
Whatever you're going through, I'm here to listen and support you!

💪 **Quick Coping Strategies:**
• 🌬️ Deep breathing - 4 seconds in, 6 seconds out
• 📝 Journal your thoughts - get them out of your head
• 🚶 Take a walk - fresh air works wonders
• 🎵 Listen to music - soothe your soul

🌈 **Remember:**
• Your feelings are valid
• It's okay to not be okay
• Small steps lead to big changes

**Want to talk about what's on your mind? I'm here to listen!** 💬
        """
        
        await update.message.reply_text(support_text, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def provide_lifestyle_tips(self, update: Update, user_id: int):
        """Provide lifestyle and wellness tips"""
        tips = random.choice([
            "🏋️ **Move Your Body!**\nEven 10-minute walks boost mood and energy! 🚶‍♂️",
            "💧 **Hydration Station!**\nDrink water first thing in the morning! 🌊",
            "😴 **Sleep Superpower!**\nQuality sleep is secret wellness weapon! 🌙",
            "🍎 **Eat the Rainbow!**\nColorful foods = diverse nutrients! 🌈",
            "🧘 **Mindfulness Moment!**\nPause and breathe deeply 3 times! 🌬️"
        ])
        
        await update.message.reply_text(tips, parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def generate_health_report(self, update: Update, user_id: int):
        """Generate comprehensive health report"""
        if not self.chat_history.get(user_id):
            await update.message.reply_text("📊 Let's chat more to build your personalized health report! 💬")
            return CHAT_DIAGNOSIS
        
        await update.message.reply_chat_action("typing")
        await asyncio.sleep(3)
        
        report = await self.get_comprehensive_health_report(
            self.chat_history[user_id],
            self.user_profiles.get(user_id, {})
        )
        
        await update.message.reply_text(
            f"📊 **Your Ultimate Health Report** 🎉\n\n{report}",
            parse_mode='Markdown'
        )
        return CHAT_DIAGNOSIS

    async def share_fun_fact(self, update: Update, user_id: int):
        """Share fun health facts"""
        facts = [
            "🤓 **Fun Fact:** Laughing boosts your immune system and reduces stress! 😄",
            "🧠 **Brainy Bit:** Your brain generates enough electricity to power a small light bulb! 💡",
            "❤️ **Heart Smart:** A woman's heart beats faster than a man's! 💓",
            "👃 **Nose Knows:** Your nose can remember 50,000 different scents! 🌸",
            "🦷 **Tooth Truth:** Tooth enamel is the hardest substance in the human body! 💎"
        ]
        
        await update.message.reply_text(random.choice(facts), parse_mode='Markdown')
        return CHAT_DIAGNOSIS

    async def return_to_main_menu(self, update: Update, user_id: int):
        """Return to main menu"""
        if user_id in self.chat_history:
            self.chat_history[user_id] = []
        
        await update.message.reply_text(
            "🏠 **Welcome back to Main Menu!**\n\nWhat would you like to explore next? 🎉",
            reply_markup=ReplyKeyboardMarkup([["🏠 Main Menu"]], resize_keyboard=True)
        )
        await self.start_command(update, None)

    # Additional feature handlers
    async def quick_health_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick health assessment"""
        keyboard = [
            [KeyboardButton("🤒 Common Symptoms"), KeyboardButton("😊 General Wellness")],
            [KeyboardButton("🧠 Mental Check"), KeyboardButton("🏋️ Fitness Advice")],
            [KeyboardButton("🍎 Nutrition Tips"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🎯 **Quick Health Check**\n\nWhat area would you like to assess?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def mental_wellness(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mental wellness center"""
        keyboard = [
            [KeyboardButton("😔 Stress Help"), KeyboardButton("😴 Sleep Issues")],
            [KeyboardButton("🎯 Anxiety Tips"), KeyboardButton("🌈 Mood Boosters")],
            [KeyboardButton("🧘 Mindfulness"), KeyboardButton("🏠 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🧠 **Mental Wellness Center** 🌈\n\nHow can I support your mental health today?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def health_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Health-related fun activities"""
        games = [
            "🎮 **Health Trivia:** Did you know? Taking stairs burns more calories than jogging! 🏃‍♂️",
            "🤔 **Mystery Symptom:** I'm thinking of a symptom that gets better with rest... what is it? 💭",
            "🏆 **Wellness Challenge:** Drink one extra glass of water today! 💧",
            "🎯 **Health Quiz:** True or False: Bananas can help with muscle cramps? 🍌",
            "🌈 **Mood Booster:** Name 3 things you're grateful for today! ✨"
        ]
        
        await update.message.reply_text(random.choice(games), parse_mode='Markdown')

    async def handle_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Master message handler"""
        text = update.message.text
        
        # Main menu options
        if text == "🗣️ Chat with Dr. AI":
            return await self.start_chat_diagnosis(update, context)
        elif text == "🎯 Quick Health Check":
            await self.quick_health_check(update, context)
        elif text == "🧠 Mental Wellness":
            await self.mental_wellness(update, context)
        elif text == "🏋️ Lifestyle Tips":
            await self.provide_lifestyle_tips(update, update.effective_user.id)
        elif text == "🩺 First Aid Guide":
            await self.handle_first_aid(update, context)
        elif text == "📚 Health Library":
            await self.handle_health_library(update, context)
        elif text == "🎮 Health Games":
            await self.health_games(update, context)
        elif text == "📊 My Health Report":
            user_id = update.effective_user.id
            if self.chat_history.get(user_id):
                await self.generate_health_report(update, user_id)
            else:
                await update.message.reply_text("📊 Let's chat first to build your health report! Try 'Chat with Dr. AI' 🗣️")
        elif text == "🏠 Main Menu":
            await self.start_command(update, context)
        else:
            # If not in conversation, suggest starting one
            await update.message.reply_text(
                "🤖 **Hey there!** 👋\n\nI'm RAGnosis AI, your fun health companion! "
                "Try `🗣️ Chat with Dr. AI` to start a conversation about your health, "
                "or explore other features from the menu! 🎉",
                parse_mode='Markdown'
            )

    # Existing utility methods (simplified)
    async def handle_first_aid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """First aid guide"""
        await update.message.reply_text(
            "🩺 **Quick First Aid Tips** 🚑\n\n"
            "For emergencies: CALL LOCAL EMERGENCY NUMBER\n\n"
            "• 🤕 Cuts: Apply pressure with clean cloth\n"
            "• 🔥 Burns: Cool with running water 10-20 mins\n"
            "• 🤢 Poisoning: Call poison control immediately\n"
            "• 💓 CPR: Push hard and fast in center of chest\n\n"
            "*Always seek professional help for serious injuries!*",
            parse_mode='Markdown'
        )

    async def handle_health_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Health information library"""
        await update.message.reply_text(
            "📚 **Health Library** 🏥\n\n"
            "I can provide info on:\n"
            "• Common illnesses and symptoms\n"
            "• Wellness and prevention tips\n"
            "• Mental health information\n"
            "• Nutrition and exercise guidance\n\n"
            "Try chatting with me about any health topic! 🗣️",
            parse_mode='Markdown'
        )

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel any conversation"""
        user_id = update.effective_user.id
        await self.return_to_main_menu(update, user_id)
        return ConversationHandler.END

def main():
    """Launch the ultimate RAGnosis AI"""
    print("🚀 LAUNCHING RAGNOSIS AI ULTIMATE EDITION...")
    print("🎉 Featuring: Dynamic Chat + Emotional Support + Health Games + Fun Personality!")
    
    ragnosis_ai = RagnosisAI()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ULTIMATE Conversation Handler - FIXED AND WORKING
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🗣️ Chat with Dr\. AI$'), ragnosis_ai.start_chat_diagnosis),
            MessageHandler(filters.Regex('^🧠 Mental Wellness$'), ragnosis_ai.start_chat_diagnosis),
            MessageHandler(filters.Regex('^🏋️ Lifestyle Tips$'), ragnosis_ai.start_chat_diagnosis)
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
            CommandHandler('cancel', ragnosis_ai.cancel_conversation),
            MessageHandler(filters.Regex('^🏠 Main Menu$'), ragnosis_ai.cancel_conversation),
            MessageHandler(filters.Regex('^🎯 Get Analysis$'), ragnosis_ai.handle_chat_message),
            MessageHandler(filters.Regex('^🧠 Emotional Support$'), ragnosis_ai.handle_chat_message),
            MessageHandler(filters.Regex('^🏋️ Lifestyle Tips$'), ragnosis_ai.handle_chat_message),
            MessageHandler(filters.Regex('^📊 Health Report$'), ragnosis_ai.handle_chat_message),
            MessageHandler(filters.Regex('^🎮 Fun Fact$'), ragnosis_ai.handle_chat_message)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True
    )
    
    # Add all handlers
    application.add_handler(CommandHandler("start", ragnosis_ai.start_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ragnosis_ai.handle_all_messages))
    
    print("✅ ULTIMATE RAGnosis AI READY!")
    print("🎊 Features: Working Chat + Emotional Support + Health Games + Dynamic Personality!")
    print("🤖 Bot is now running...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()