# bot_runner.py - Simple Railway runner
import asyncio
import os
from main import DynamicRagnosisBot

async def main():
    # Validate environment variables
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found!")
        return
    
    print("🚀 Starting RAGnosis Bot on Railway...")
    bot = DynamicRagnosisBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
