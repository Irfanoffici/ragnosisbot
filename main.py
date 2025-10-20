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

    # ... [KEEP ALL YOUR EXISTING METHODS EXACTLY AS THEY ARE] ...
    # Your existing start_command, handle_chat_message, etc. methods remain the same
    # ... [ALL YOUR EXISTING CODE] ...

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
