# railway_runner.py - Simple Railway runner
import asyncio
import os
import logging
from main import DynamicRagnosisBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        print("🚀 Starting RAGnosis Bot on Railway...")
        
        # Validate environment variables
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            raise ValueError("TELEGRAM_BOT_TOKEN not found!")
        
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY not found!")
        
        bot = DynamicRagnosisBot()
        await bot.run()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        # Keep the process alive for Railway to see the error
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
