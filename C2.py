जय श्री राम  

Below is an **expanded** solution that incorporates:

1. **Security** (environment variables for secrets).  
2. **Scalability** (Dockerfile example, mention of cloud MongoDB).  
3. **Error Handling** with more `try/except` blocks and user-friendly messages.  
4. **Referrals & Analytics** (basic referral system placeholders, analytics idea).  
5. **Translations & Sentiment** (placeholder functions for language translation and sentiment analysis).

> **Important**: This code is a **conceptual guide**. You should adapt, refine, and test it thoroughly in your real environment.

---

## 1. Directory Structure Example

```
telegram-ai-bot/
├── Dockerfile
├── README.md
├── requirements.txt
├── app.py
├── analytics.py        # optional analytics script or web app
└── .env               # store environment variables securely (never commit this)
```

---

## 2. `.env` (Environment Variables)

```bash
# Example .env file
TELEGRAM_BOT_TOKEN="<YOUR-TELEGRAM-BOT-TOKEN>"
MONGO_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority"
GEMINI_API_KEY="<YOUR-GEMINI-API-KEY>"
REFERRAL_BONUS=10
```

- **Never commit** `.env` files to Git. Use `.gitignore` to exclude it.

---

## 3. `Dockerfile`

```dockerfile
# Python 3.10 base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port if you need a web server for analytics
# EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
```

> **Build & Run**:
> ```bash
> docker build -t telegram-ai-bot .
> docker run -d --env-file .env --name telegram-bot telegram-ai-bot
> ```

---

## 4. `requirements.txt` (Example)

```
python-telegram-bot==20.3
pymongo==4.5.0
google-generativeai==0.1.0
aiohttp==3.8.4
python-dotenv==1.0.0
googletrans==4.0.0-rc1
textblob==0.17.1   # For a simple sentiment analysis demo
```

---

## 5. `app.py` (Main Bot Logic)

```python
import os
import logging
import asyncio
import datetime

# Telegram bot imports
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)

# Mongo + Gemini + Additional libs
import google.generativeai as palm
from pymongo import MongoClient
import aiohttp

# Dotenv for environment variables
from dotenv import load_dotenv

# Translation & Sentiment (demo placeholders)
from googletrans import Translator
from textblob import TextBlob

# Load environment variables from .env
load_dotenv()

# -----------------------------------------------------------------------------
# 1. Setup Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 2. Environment Variables
# -----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "0"))

# -----------------------------------------------------------------------------
# 3. Initialize MongoDB and Gemini
# -----------------------------------------------------------------------------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_ai_bot"]

palm.configure(api_key=GEMINI_API_KEY)

# -----------------------------------------------------------------------------
# 4. Utility: Translation & Sentiment (Placeholders)
# -----------------------------------------------------------------------------
def translate_text(text: str, target_lang: str = "en") -> str:
    """Translate user text to a target language using googletrans."""
    try:
        translator = Translator()
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        logger.exception("Translation error")
        return text  # fallback: return original if fail

def analyze_sentiment(text: str) -> str:
    """Analyze sentiment using a simple approach with TextBlob."""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0:
            return "positive"
        elif polarity < 0:
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        logger.exception("Sentiment analysis error")
        return "unknown"

# -----------------------------------------------------------------------------
# 5. Referral Logic (Placeholder)
# -----------------------------------------------------------------------------
def generate_referral_code(chat_id: int) -> str:
    """Generate a unique referral code (simplistic example)."""
    return f"REF{chat_id}"

async def process_referral(referral_code: str, new_user_id: int):
    """
    If referral_code is valid, give bonus to the referrer and new user.
    Here we store bonus points or some usage credit in the DB.
    """
    try:
        # Example: referral code is "REF<chat_id>"
        # Let's parse the referred chat_id
        if not referral_code.startswith("REF"):
            return

        referrer_id = int(referral_code.replace("REF", ""))

        referrer_user = db.users.find_one({"chat_id": referrer_id})
        new_user = db.users.find_one({"chat_id": new_user_id})

        if referrer_user and new_user:
            # Add bonus to both
            db.users.update_one(
                {"chat_id": referrer_id},
                {"$inc": {"bonus_points": REFERRAL_BONUS}}
            )
            db.users.update_one(
                {"chat_id": new_user_id},
                {"$inc": {"bonus_points": REFERRAL_BONUS}}
            )
    except Exception as e:
        logger.exception("Error processing referral")

# -----------------------------------------------------------------------------
# 6. /start Command Handler
# -----------------------------------------------------------------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /start command:
    - Registers new user if not exist
    - Asks for phone number
    - Checks for referral code in arguments (optional).
    """
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user

        # Check if user already exists
        existing_user = db.users.find_one({"chat_id": chat_id})
        if existing_user:
            await update.message.reply_text("Welcome back! You're already registered.")
            return

        # Check referral argument (if any)
        referral_code = None
        if context.args:
            referral_code = context.args[0]

        # Insert new user
        user_data = {
            "chat_id": chat_id,
            "username": user.username,
            "first_name": user.first_name,
            "phone": None,
            "bonus_points": 0,
            "created_at": datetime.datetime.utcnow()
        }
        db.users.insert_one(user_data)

        # If referral code, process it
        if referral_code:
            await process_referral(referral_code, new_user_id=chat_id)

        # Ask for contact info
        contact_button = KeyboardButton(text="Share Contact", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True)
        await update.message.reply_text(
            "Hi there! Please share your phone number to complete registration.",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.exception("Error in start_handler")
        await update.message.reply_text("An error occurred while starting. Please try again later.")

# -----------------------------------------------------------------------------
# 7. Contact/Phone Number Handler
# -----------------------------------------------------------------------------
async def contact_handler(update: Update, context: CallbackContext):
    """Stores the phone number from the contact button."""
    try:
        message = update.message
        if message.contact:
            phone_number = message.contact.phone_number
            chat_id = message.chat_id

            db.users.update_one(
                {"chat_id": chat_id},
                {"$set": {"phone": phone_number}}
            )

            # Also generate a personal referral code for the user
            referral_code = generate_referral_code(chat_id)
            db.users.update_one(
                {"chat_id": chat_id},
                {"$set": {"referral_code": referral_code}}
            )

            await message.reply_text(
                f"Thanks! We have your phone number: {phone_number}. "
                f"Your personal referral code is {referral_code}. Share it with friends to earn bonuses!",
                reply_markup=None
            )
    except Exception as e:
        logger.exception("Error in contact_handler")
        await update.message.reply_text("Unable to process contact. Please try again.")

# -----------------------------------------------------------------------------
# 8. Gemini-Powered Chat (Text Messages)
# -----------------------------------------------------------------------------
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives user text, optional translation, sends to Gemini, stores conversation."""
    try:
        user_text = update.message.text
        chat_id = update.effective_chat.id

        # 1) Translate user message to English if needed
        #    Example scenario: if we want to analyze in English.
        translated_text = translate_text(user_text, target_lang="en")

        # 2) Analyze sentiment (simple approach)
        sentiment_result = analyze_sentiment(translated_text)

        # 3) Store user query
        message_doc = {
            "chat_id": chat_id,
            "message_type": "user_text",
            "original_text": user_text,
            "translated_text": translated_text,
            "sentiment": sentiment_result,
            "timestamp": datetime.datetime.utcnow()
        }
        db.messages.insert_one(message_doc)

        # 4) Call Gemini for response
        try:
            palm_response = palm.generate_text(
                model="models/text-bison-001",
                prompt=translated_text,
                temperature=0.2
            )
            gemini_text = palm_response.result if palm_response else "No response from Gemini."
        except Exception as e:
            logger.exception("Gemini API error")
            gemini_text = "Sorry, I'm having trouble connecting to the AI service."

        # 5) Store Gemini response
        response_doc = {
            "chat_id": chat_id,
            "message_type": "gemini_response",
            "text": gemini_text,
            "timestamp": datetime.datetime.utcnow()
        }
        db.messages.insert_one(response_doc)

        # 6) Possibly translate response back to user’s language
        #    For example, if we detect user language is Spanish, etc.
        #    Let's assume we just echo in English for now.
        await update.message.reply_text(gemini_text)

    except Exception as e:
        logger.exception("Error in text_message_handler")
        await update.message.reply_text("An error occurred while processing your message. Please try again.")

# -----------------------------------------------------------------------------
# 9. Image/File Analysis Handler
# -----------------------------------------------------------------------------
async def file_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles images or documents, describes them with Gemini, and stores metadata."""
    try:
        chat_id = update.effective_chat.id
        file_id = None
        file_type = None
        description = "No description"

        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"
        else:
            return

        # Download the file
        new_file = await context.bot.get_file(file_id)
        file_path = f"{file_id}.jpg" if file_type == "photo" else update.message.document.file_name
        await new_file.download_to_drive(custom_path=file_path)

        # Analyze file (very simplistic approach)
        prompt_text = f"Describe the file named: {file_path}."
        try:
            palm_response = palm.generate_text(
                model="models/text-bison-001",
                prompt=prompt_text
            )
            description = palm_response.result if palm_response else "No description from Gemini."
        except Exception as e:
            logger.exception("Gemini API error (file analysis)")
            description = "Could not describe the file."

        # Save file metadata
        file_doc = {
            "chat_id": chat_id,
            "file_id": file_id,
            "file_name": file_path,
            "file_type": file_type,
            "description": description,
            "timestamp": datetime.datetime.utcnow()
        }
        db.files.insert_one(file_doc)

        # Reply
        await update.message.reply_text(
            f"File '{file_path}' analysis:\n{description}"
        )

    except Exception as e:
        logger.exception("Error in file_message_handler")
        await update.message.reply_text("An error occurred while processing the file. Please try again.")

# -----------------------------------------------------------------------------
# 10. Web Search Command (/websearch)
# -----------------------------------------------------------------------------
async def websearch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /websearch command. Usage: /websearch <search query>"""
    try:
        chat_id = update.effective_chat.id
        args = context.args

        if not args:
            await update.message.reply_text("Usage: /websearch <search query>")
            return

        query = " ".join(args)

        # Perform search
        try:
            search_results = await perform_web_search(query)
            summary = await summarize_results_with_gemini(query, search_results)
        except Exception as e:
            logger.exception("Error performing web search or summarization")
            await update.message.reply_text("Error performing web search.")
            return

        # Format and store
        response_text = f"**Summary**:\n{summary}\n\n**Top Links**:\n"
        for i, link in enumerate(search_results[:5], 1):
            response_text += f"{i}. {link}\n"

        search_doc = {
            "chat_id": chat_id,
            "query": query,
            "summary": summary,
            "links": search_results[:5],
            "timestamp": datetime.datetime.utcnow()
        }
        db.websearch.insert_one(search_doc)

        await update.message.reply_text(response_text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error in websearch_handler")
        await update.message.reply_text("An error occurred. Please try again later.")

# -----------------------------------------------------------------------------
# 11. Helper Functions: Web Search & Summaries
# -----------------------------------------------------------------------------
async def perform_web_search(query: str):
    """Perform a web search and return a list of top result URLs (dummy placeholder)."""
    # Replace this with real logic (Google Custom Search, Bing API, etc.)
    return [
        f"https://example.com/search?q={query}1",
        f"https://example.com/search?q={query}2",
        f"https://example.com/search?q={query}3",
        f"https://example.com/search?q={query}4",
        f"https://example.com/search?q={query}5",
    ]

async def summarize_results_with_gemini(query: str, links: list):
    """Use Gemini (PaLM) to summarize top links for the query."""
    summary_prompt = f"""
        I searched the web for "{query}" and found the following links:
        {links}

        Please provide a concise summary of the information relevant to this query.
    """
    try:
        palm_response = palm.generate_text(
            model="models/text-bison-001",
            prompt=summary_prompt,
            temperature=0.2
        )
        return palm_response.result if palm_response else "No summary"
    except Exception:
        logger.exception("Error calling Gemini for summary")
        return "No summary available"

# -----------------------------------------------------------------------------
# 12. Main Function: Set up Handlers & Start Bot
# -----------------------------------------------------------------------------
def main():
    # 1) Build the application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 2) Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("websearch", websearch_handler))

    # Contact handler
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # File handlers
    file_filter = (filters.Document.ALL | filters.PHOTO)
    application.add_handler(MessageHandler(file_filter, file_message_handler))

    # Text handler (fallback for anything else that’s text)
    text_filter = filters.TEXT & (~filters.COMMAND)
    application.add_handler(MessageHandler(text_filter, text_message_handler))

    # 3) Start polling
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
```

---

## 6. (Optional) `analytics.py`
```python
"""
Example: a simple script to display analytics from the DB.
Run as a separate process or integrate into a Flask/Node.js app with a web UI.
"""

import os
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_ai_bot"]

def show_analytics():
    total_users = db.users.count_documents({})
    total_messages = db.messages.count_documents({})
    total_files = db.files.count_documents({})
    total_websearches = db.websearch.count_documents({})

    print(f"Total Users: {total_users}")
    print(f"Total Messages: {total_messages}")
    print(f"Total Files Analyzed: {total_files}")
    print(f"Total Websearches: {total_websearches}")

if __name__ == "__main__":
    show_analytics()
```

> You could expand this with more sophisticated queries, or build a Flask app that renders charts using `Chart.js` or similar.

---

## **Key Points to Remember**

1. **Security**:  
   - Store secrets in `.env` (not in code).  
   - Use `python-dotenv` to load them.  
   - Keep `.env` out of version control.

2. **Scalability**:  
   - Dockerize your application with the provided `Dockerfile`.  
   - Deploy to services like AWS ECS, Heroku, etc.  
   - Use **MongoDB Atlas** for a reliable cloud database.

3. **Error Handling**:  
   - Surround critical operations with `try/except`.  
   - Provide user-friendly messages when exceptions occur.  
   - Log exceptions for debugging.

4. **Referrals & Analytics**:  
   - Implement a referral system with a unique code (`REF<chat_id>` in this example).  
   - Track usage stats in separate collections.  
   - Provide an analytics dashboard or scripts to monitor usage.

5. **Translations & Sentiment**:  
   - `googletrans` for quick translations, `textblob` or advanced NLP for sentiment.  
   - Adapt your flow if you want to handle multi-language interactions or tone analysis.  

---

This expanded setup should help you:

- Keep your bot credentials safe,  
- Scale via Docker and cloud,  
- Implement more robust error handling,  
- Track referrals/analytics,  
- And incorporate translations & sentiment analysis into your Telegram AI Chatbot. 

Happy building!
