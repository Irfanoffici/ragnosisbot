# ragnosis_bot.py
import os
import logging
import requests
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from telegram import (
    Update, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler,
    CallbackQueryHandler
)
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Conversation states
SYMPTOMS, AGE, GENDER, DURATION, SEVERITY, MEDICAL_HISTORY = range(6)

class RagnosisBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # User sessions storage (in production, use database)
        self.user_sessions = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command for RAGnosis"""
        user = update.effective_user
        
        welcome_text = f"""
🔬 *Welcome to RAGnosis, {user.first_name}!*

*Revolutionary AI-Powered Medical Assistance*

🤖 *Powered by:* Google Gemini AI + Medical RAG System

💡 *What I Offer:*
• 🧠 **Smart Symptom Analysis** - AI-driven diagnosis assistance
• 💊 **Medication Intelligence** - Drug info & interactions
• 📊 **Health Insights** - Personalized recommendations
• 🚨 **Emergency Guidance** - First aid & urgent care
• 📚 **Medical Knowledge** - Latest research & information
• 🔍 **Condition Explorer** - Deep dive into health topics

⚡ *Quick Access Below* 👇
        """
        
        keyboard = [
            [KeyboardButton("🔍 Symptom Analysis"), KeyboardButton("💊 Drug Info")],
            [KeyboardButton("🚨 Emergency Guide"), KeyboardButton("📊 Health Insights")],
            [KeyboardButton("📚 Learn More"), KeyboardButton("🆘 Immediate Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Choose your medical need...")
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def quick_symptom_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start smart symptom analysis"""
        common_symptoms = [
            ["🤒 Fever & Chills", "🤧 Cough & Cold", "🤕 Headache"],
            ["🤢 Nausea & Vomit", "💨 Breathing Issues", "😴 Fatigue"],
            ["🩸 Bleeding", "🔥 Pain", "🌡️ Other Symptoms"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(common_symptoms, resize_keyboard=True)
        await update.message.reply_text(
            "🔍 *RAGnosis Symptom Analysis*\n\n*Select your primary symptoms:*\n\nI'll use AI to analyze potential conditions and provide guidance.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return SYMPTOMS

    async def collect_symptoms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect detailed symptoms"""
        user_id = update.effective_user.id
        symptoms = update.message.text
        
        # Initialize user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        self.user_sessions[user_id]['symptoms'] = symptoms
        
        # Age selection with better options
        age_options = [
            [KeyboardButton("👶 Child (0-12)"), KeyboardButton("👦 Teen (13-17)")],
            [KeyboardButton("👨 Adult (18-40)"), KeyboardButton("👨‍💼 Middle (41-65)")],
            [KeyboardButton("👴 Senior (65+)"), KeyboardButton("🚫 Skip Age")]
        ]
        reply_markup = ReplyKeyboardMarkup(age_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "👤 *Patient Age Group*\n\n*Select age for accurate analysis:*\n\nAge helps determine condition probabilities and recommendations.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return AGE

    async def collect_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect age and ask for gender"""
        user_id = update.effective_user.id
        age_group = update.message.text
        self.user_sessions[user_id]['age_group'] = age_group
        
        gender_options = [
            [KeyboardButton("👨 Male"), KeyboardButton("👩 Female")],
            [KeyboardButton("⚧ Other"), KeyboardButton("🚫 Prefer not to say")]
        ]
        reply_markup = ReplyKeyboardMarkup(gender_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "👤 *Biological Sex*\n\n*This affects condition probabilities:*\n\nSome conditions are more common in specific sexes.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return GENDER

    async def collect_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect gender and ask for duration"""
        user_id = update.effective_user.id
        gender = update.message.text
        self.user_sessions[user_id]['gender'] = gender
        
        duration_options = [
            [KeyboardButton("⏱️ <24 hours"), KeyboardButton("🕐 1-3 days")],
            [KeyboardButton("🕑 3-7 days"), KeyboardButton("🕒 1-4 weeks")],
            [KeyboardButton("🕓 >1 month"), KeyboardButton("❓ Not sure")]
        ]
        reply_markup = ReplyKeyboardMarkup(duration_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "⏰ *Symptom Duration*\n\n*How long have you experienced these symptoms?*\n\nDuration helps distinguish acute vs chronic conditions.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return DURATION

    async def collect_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect duration and ask for severity"""
        user_id = update.effective_user.id
        duration = update.message.text
        self.user_sessions[user_id]['duration'] = duration
        
        severity_options = [
            [KeyboardButton("😊 Mild"), KeyboardButton("😐 Moderate")],
            [KeyboardButton("😫 Severe"), KeyboardButton("🚨 Critical")]
        ]
        reply_markup = ReplyKeyboardMarkup(severity_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "📊 *Symptom Severity*\n\n*How severe are your symptoms?*\n\nThis determines urgency and recommended actions.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return SEVERITY

    async def collect_severity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect severity and ask for medical history"""
        user_id = update.effective_user.id
        severity = update.message.text
        self.user_sessions[user_id]['severity'] = severity
        
        history_options = [
            [KeyboardButton("💊 Chronic Conditions"), KeyboardButton("🔄 Recurring Issue")],
            [KeyboardButton("🆕 New Symptoms"), KeyboardButton("🚫 No History")]
        ]
        reply_markup = ReplyKeyboardMarkup(history_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "📋 *Medical Context*\n\n*Any relevant medical history?*\n\nThis helps provide personalized recommendations.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return MEDICAL_HISTORY

    async def perform_ai_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Perform comprehensive AI analysis using Gemini"""
        user_id = update.effective_user.id
        medical_history = update.message.text
        self.user_sessions[user_id]['medical_history'] = medical_history
        
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        try:
            # Get all collected data
            user_data = self.user_sessions.get(user_id, {})
            
            # Create comprehensive prompt for Gemini
            analysis_prompt = f"""
            ACT as RAGnosis - an advanced AI medical diagnostic assistant. Analyze this patient case comprehensively:

            PATIENT PROFILE:
            - Primary Symptoms: {user_data.get('symptoms', 'Not specified')}
            - Age Group: {user_data.get('age_group', 'Not specified')}
            - Biological Sex: {user_data.get('gender', 'Not specified')}
            - Symptom Duration: {user_data.get('duration', 'Not specified')}
            - Severity Level: {user_data.get('severity', 'Not specified')}
            - Medical Context: {user_data.get('medical_history', 'Not specified')}

            PROVIDE A STRUCTURED MEDICAL ANALYSIS:

            🔍 **IMMEDIATE ASSESSMENT**
            [List 3-4 most probable conditions with likelihood percentages and brief explanations]

            📊 **SYMPTOM INTERPRETATION**
            [Break down what each symptom might indicate medically]

            🚨 **URGENCY CLASSIFICATION**
            [Specify: Emergency/Critical/Urgent/Non-urgent with clear criteria]

            💡 **IMMEDIATE ACTIONS**
            [Step-by-step recommended actions based on severity]

            🏥 **MEDICAL CONSULTATION GUIDANCE**
            [When to see a doctor, what type of specialist, what to mention]

            🏠 **HOME CARE RECOMMENDATIONS**
            [Practical self-care tips if condition is non-urgent]

            🔬 **POSSIBLE DIAGNOSTIC PATH**
            [What tests or examinations might be needed]

            ⚠️ **RED FLAG WATCHLIST**
            [Specific symptoms that warrant immediate medical attention]

            Format with appropriate emojis, be compassionate but factual, and emphasize this is AI assistance not medical diagnosis.
            """

            # Call Gemini AI
            ai_response = await self.call_gemini_ai(analysis_prompt)
            
            # Generate personalized recommendations
            recommendations = await self.generate_personalized_recommendations(user_data)
            
            # Format final response
            final_response = f"""
{ai_response}

{recommendations}

🔬 *RAGnosis AI Analysis Complete*

💡 *Next Steps:*
1. Review the analysis above
2. Follow recommended actions based on urgency
3. Consult healthcare professional for definitive diagnosis
4. Use /track to monitor symptom changes

⚠️ *Medical Disclaimer:*
This AI analysis is for informational purposes only. I am an AI assistant, not a medical doctor. Always consult qualified healthcare professionals for medical diagnosis and treatment. In emergencies, call your local emergency number immediately.

🔄 *Want to analyze different symptoms? Use /symptoms*
            """
            
            # Clear user session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            # Show main menu
            await self.show_main_menu(update)
            
            # Send analysis (split if too long)
            if len(final_response) > 4096:
                chunks = [final_response[i:i+4096] for i in range(0, len(final_response), 4096)]
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                await update.message.reply_text(final_response, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            await update.message.reply_text(
                "❌ *Analysis Error*\n\nI encountered an issue processing your symptoms. Please try again or use /start to begin fresh.",
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END

    async def call_gemini_ai(self, prompt: str) -> str:
        """Call Gemini AI with enhanced error handling"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return """
🔍 *RAGnosis AI Analysis*

Based on your symptoms, here's a general assessment:

🤒 **Common Possibilities:**
Various conditions could cause these symptoms. The specific combination, duration, and severity are important for accurate assessment.

🏥 **General Recommendation:**
Consult a healthcare professional for proper evaluation. They can consider your full medical history and perform necessary examinations.

💡 **Immediate Actions:**
• Monitor symptoms closely
• Note any changes in severity
• Keep hydrated and rest if appropriate
• Avoid self-medication without professional advice

🚨 **Seek Immediate Care if you experience:**
• Difficulty breathing
• Severe pain
• High fever that doesn't improve
• Confusion or dizziness
• Any concerning symptom progression
            """

    async def generate_personalized_recommendations(self, user_data: dict) -> str:
        """Generate personalized health recommendations"""
        prompt = f"""
        Based on this patient profile, provide personalized health recommendations:
        
        Patient Data: {user_data}
        
        Provide 3-5 personalized health recommendations considering their age, symptoms, and severity.
        Focus on practical, actionable advice.
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return f"💫 *Personalized Recommendations:*\n\n{response.text}"
        except:
            return "💫 *General Health Tips:*\n• Maintain regular health check-ups\n• Stay hydrated and eat balanced meals\n• Get adequate rest and sleep\n• Monitor symptoms and seek help if worsening"

    async def drug_information(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Provide drug/medication information"""
        await update.message.reply_text(
            "💊 *RAGnosis Drug Intelligence*\n\n*Enter medication name for detailed information:*\n\nI'll provide:\n• Uses and indications\n• Dosage guidelines\n• Side effects\n• Interactions\n• Precautions\n\n*Examples:* Aspirin, Metformin, Amoxicillin, Ibuprofen",
            parse_mode='Markdown'
        )

    async def emergency_guide(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Emergency and first aid guidance"""
        emergency_options = [
            [KeyboardButton("🫀 Heart Attack"), KeyboardButton("💨 Choking")],
            [KeyboardButton("🔥 Burns"), KeyboardButton("🩸 Severe Bleeding")],
            [KeyboardButton("🤕 Head Injury"), KeyboardButton("🔙 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(emergency_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "🚨 *RAGnosis Emergency Guide*\n\n*Select emergency situation:*\n\nI'll provide step-by-step first aid guidance.\n\n⚠️ *Remember:* Always call local emergency services first!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_emergency_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle specific emergency situations"""
        emergency_type = update.message.text
        
        emergency_guides = {
            "🫀 Heart Attack": """
🫀 *Heart Attack - Emergency Response*

🚨 *IMMEDIATE ACTIONS:*
1. 📞 **CALL EMERGENCY SERVICES NOW**
2. 💊 Chew aspirin (if available and not allergic)
3. 🛌 Sit or lie down in comfortable position
4. 👕 Loosen tight clothing
5. ❌ Do NOT drive yourself to hospital

🎯 *Recognize Symptoms:*
• Chest pain/pressure
• Pain in arms, back, neck, jaw
• Shortness of breath
• Nausea, cold sweat
• Lightheadedness

⏱️ *Time is critical - act immediately!*
            """,
            "💨 Choking": """
💨 *Choking - Emergency Response*

🚨 *For CONSCIOUS Person:*
1. 📞 **Call emergency services**
2. 🤲 Perform Heimlich maneuver
3. ↗️ Give 5 back blows between shoulder blades
4. 🔄 Alternate between back blows and abdominal thrusts

🎯 *Signs of Choking:*
• Can't speak or breathe
• Clutching throat
• Turning blue
• Panicked behavior

⚠️ *If person becomes unconscious, begin CPR*
            """
        }
        
        if emergency_type in emergency_guides:
            await update.message.reply_text(emergency_guides[emergency_type], parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "🚨 *Emergency Principle:*\n\n1. 📞 **Call local emergency number immediately**\n2. 🛌 **Keep person calm and still**\n3. 💊 **Follow dispatcher instructions**\n4. 🏥 **Prepare for ambulance arrival**",
                parse_mode='Markdown'
            )

    async def health_insights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Provide health insights and tips"""
        insights_text = """
📊 *RAGnosis Health Insights*

🌡️ *Daily Health Tips:*
• 💧 **Hydration:** Drink 8 glasses of water daily
• 🏃 **Activity:** 30 minutes moderate exercise
• 🥗 **Nutrition:** Balanced diet with fruits/vegetables
• 😴 **Sleep:** 7-9 hours quality sleep
• 🧘 **Stress:** Practice daily relaxation

🔍 *Preventive Care:*
• Regular health check-ups
• Vaccinations up to date
• Dental and vision exams
• Cancer screenings as recommended

💡 *Wellness Reminders:*
• Wash hands frequently
• Practice good posture
• Take screen breaks
• Stay socially connected

*Your health journey matters!* 🌟
        """
        await update.message.reply_text(insights_text, parse_mode='Markdown')

    async def learn_more(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Educational medical content"""
        learn_options = [
            [KeyboardButton("🧠 Mental Health"), KeyboardButton("❤️ Heart Health")],
            [KeyboardButton("🫁 Respiratory"), KeyboardButton("🦠 Infectious")],
            [KeyboardButton("📖 Health Basics"), KeyboardButton("🔙 Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(learn_options, resize_keyboard=True)
        
        await update.message.reply_text(
            "📚 *RAGnosis Medical Library*\n\n*Choose a health topic to learn more:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def immediate_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Immediate help and crisis resources"""
        help_text = """
🆘 *RAGnosis Immediate Help*

🚨 *Emergency Numbers:*
• 🏥 **Medical Emergency:** 112/911/999
• 🧠 **Mental Health Crisis:** Local crisis line
• 🐾 **Poison Control:** Local poison center

💡 *When to Seek Immediate Help:*
• Chest pain or pressure
• Difficulty breathing
• Severe bleeding
• Sudden weakness or numbness
• Suicidal thoughts
• Severe allergic reaction

📞 *Keep these numbers saved!*

🔗 *Additional Resources:*
• Local hospital emergency department
• Primary care physician
• Urgent care centers
• Telemedicine services

*Your safety is the priority!* 🛡️
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_learning_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle specific learning topics"""
        topic = update.message.text
        
        # Use Gemini to generate educational content
        prompt = f"Provide a comprehensive but easy-to-understand educational overview about {topic} for general public. Include key facts, prevention tips, and when to see a doctor."
        
        await update.message.chat.send_action(action="typing")
        try:
            response = self.gemini_model.generate_content(prompt)
            await update.message.reply_text(
                f"📚 *{topic} - Educational Overview*\n\n{response.text}",
                parse_mode='Markdown'
            )
        except:
            await update.message.reply_text(
                f"📚 *{topic} Information*\n\nI recommend consulting reliable medical sources like WHO, CDC, or Mayo Clinic for comprehensive information about {topic}.",
                parse_mode='Markdown'
            )

    async def show_main_menu(self, update: Update):
        """Show the main menu"""
        keyboard = [
            [KeyboardButton("🔍 Symptom Analysis"), KeyboardButton("💊 Drug Info")],
            [KeyboardButton("🚨 Emergency Guide"), KeyboardButton("📊 Health Insights")],
            [KeyboardButton("📚 Learn More"), KeyboardButton("🆘 Immediate Help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "🏠 *Back to Main Menu*\n\nHow can I assist you with your health concerns?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all other messages with AI"""
        text = update.message.text
        
        if text == "💊 Drug Info":
            await self.drug_information(update, context)
        elif text == "🚨 Emergency Guide":
            await self.emergency_guide(update, context)
        elif text in ["🫀 Heart Attack", "💨 Choking", "🔥 Burns", "🩸 Severe Bleeding", "🤕 Head Injury"]:
            await self.handle_emergency_query(update, context)
        elif text == "📊 Health Insights":
            await self.health_insights(update, context)
        elif text == "📚 Learn More":
            await self.learn_more(update, context)
        elif text in ["🧠 Mental Health", "❤️ Heart Health", "🫁 Respiratory", "🦠 Infectious", "📖 Health Basics"]:
            await self.handle_learning_query(update, context)
        elif text == "🆘 Immediate Help":
            await self.immediate_help(update, context)
        elif text == "🔙 Main Menu":
            await self.show_main_menu(update)
        else:
            # Use AI for general medical questions
            await update.message.chat.send_action(action="typing")
            prompt = f"Answer this medical/health question clearly, accurately, and helpfully: {text}"
            try:
                response = self.gemini_model.generate_content(prompt)
                await update.message.reply_text(
                    f"🔬 *RAGnosis AI Response:*\n\n{response.text}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                await update.message.reply_text(
                    "❌ *I encountered an error processing your question.*\n\nPlease try rephrasing or use /start for the main menu.",
                    parse_mode='Markdown'
                )

    def setup_handlers(self, application):
        """Setup all conversation handlers"""
        
        # Main symptom analysis conversation
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^(🔍 Symptom Analysis)$"), self.quick_symptom_analysis),
                CommandHandler("symptoms", self.quick_symptom_analysis),
                CommandHandler("analyze", self.quick_symptom_analysis)
            ],
            states={
                SYMPTOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_symptoms)],
                AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_age)],
                GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_gender)],
                DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_duration)],
                SEVERITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_severity)],
                MEDICAL_HISTORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.perform_ai_analysis)],
            },
            fallbacks=[CommandHandler("cancel", self.start)]
        )
        
        # Add all handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.start))
        application.add_handler(CommandHandler("menu", self.show_main_menu))
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def run(self):
        """Run the RAGnosis bot"""
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
            return
            
        application = Application.builder().token(self.token).build()
        self.setup_handlers(application)
        
        # Bot info
        logger.info("🚀 RAGnosis AI Medical Bot is starting...")
        print("🔬 RAGnosis Bot Features:")
        print("• 🤖 Gemini AI Powered")
        print("• 🔍 Smart Symptom Analysis") 
        print("• 💊 Drug Intelligence")
        print("• 🚨 Emergency Guidance")
        print("• 📚 Medical Education")
        print("• 📱 24/7 Availability")
        print(f"• 👥 Public Access: t.me/ragnosisbot")
        
        await application.run_polling()

# Run the bot
if __name__ == "__main__":
    bot = RagnosisBot()
    asyncio.run(bot.run())
