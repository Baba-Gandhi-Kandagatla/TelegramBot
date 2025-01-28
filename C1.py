जय श्री राम

Below is a **starter** code snippet demonstrating how you might implement the Telegram AI Chatbot using:

- **python-telegram-bot** (v20+)
- **pymongo** for MongoDB
- **google.generativeai** (Gemini/PaLM 2 API)
- **aiohttp** (or requests) for web searches

> **NOTE**: This example is kept concise for demonstration. You should adapt it to your specific needs (error handling, more robust logging, etc.).  
> Make sure to install all dependencies:
> ```bash
> pip install python-telegram-bot pymongo google-generativeai aiohttp
> ```

---

## `app.py` (Main Script)

```python
import os
import logging
import asyncio
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
import google.generativeai as palm
from pymongo import MongoClient
import aiohttp
import datetime

# -----------------------------------------------------------------------------
# 1. Setup Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 2. Environment Variables (replace with your actual keys/secrets)
# -----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "<YOUR-TELEGRAM-BOT-TOKEN>")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "<YOUR-GEMINI-API-KEY>")

# -----------------------------------------------------------------------------
# 3. Initialize MongoDB and Gemini/PaLM
# -----------------------------------------------------------------------------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_ai_bot"]

# Setup Google Generative AI (Gemini/PaLM)
palm.configure(api_key=GEMINI_API_KEY)

# -----------------------------------------------------------------------------
# 4. /start Command Handler
# -----------------------------------------------------------------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command:
       - Registers new user
       - Asks for phone number via 'Contact' button.
    """
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Check if user already exists
    existing_user = db.users.find_one({"chat_id": chat_id})
    if existing_user:
        await update.message.reply_text(
            "Welcome back! You're already registered."
        )
    else:
        # Insert new user
        user_data = {
            "chat_id": chat_id,
            "username": user.username,
            "first_name": user.first_name,
            "phone": None,  # Will fill once user shares contact
            "created_at": datetime.datetime.utcnow()
        }
        db.users.insert_one(user_data)

        # Ask for contact info
        contact_button = KeyboardButton(text="Share Contact", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True)
        await update.message.reply_text(
            "Hi there! Please share your phone number to complete registration.",
            reply_markup=reply_markup
        )

# -----------------------------------------------------------------------------
# 5. Contact/Phone Number Handler
# -----------------------------------------------------------------------------
async def contact_handler(update: Update, context: CallbackContext):
    """Stores the phone number from the contact button."""
    message = update.message
    if message.contact:
        phone_number = message.contact.phone_number
        chat_id = message.chat_id

        # Update user record in MongoDB
        db.users.update_one(
            {"chat_id": chat_id},
            {"$set": {"phone": phone_number}}
        )

        await message.reply_text(
            f"Thanks! We have your phone number: {phone_number}. Registration complete!",
            reply_markup=None  # remove custom keyboard
        )

# -----------------------------------------------------------------------------
# 6. Gemini-Powered Chat (Text Messages)
# -----------------------------------------------------------------------------
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives user text, sends to Gemini, stores conversation in MongoDB."""
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # 6.1. Store user query
    message_doc = {
        "chat_id": chat_id,
        "message_type": "user_text",
        "text": user_text,
        "timestamp": datetime.datetime.utcnow()
    }
    db.messages.insert_one(message_doc)

    # 6.2. Call Gemini to get a response
    try:
        # For example, with google.generativeai:
        palm_response = palm.generate_text(
            model="models/text-bison-001",  # Example model name
            prompt=user_text,
            temperature=0.2
        )
        gemini_text = palm_response.result if palm_response else "No response from Gemini."
    except Exception as e:
        logger.exception("Error calling Gemini API")
        gemini_text = "Sorry, I'm having trouble connecting to the AI service."

    # 6.3. Store Gemini response
    response_doc = {
        "chat_id": chat_id,
        "message_type": "gemini_response",
        "text": gemini_text,
        "timestamp": datetime.datetime.utcnow()
    }
    db.messages.insert_one(response_doc)

    # 6.4. Reply to user
    await update.message.reply_text(gemini_text)

# -----------------------------------------------------------------------------
# 7. Image/File Analysis Handler
# -----------------------------------------------------------------------------
async def file_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles images or documents, describes them with Gemini, stores metadata in MongoDB."""
    chat_id = update.effective_chat.id
    file_id = None
    file_type = None
    description = "No description"

    # 7.1. Identify if it's photo or document
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
    else:
        return  # Not handled

    # 7.2. Download the file (optional)
    new_file = await context.bot.get_file(file_id)
    file_path = f"{file_id}.jpg" if file_type == "photo" else update.message.document.file_name
    await new_file.download_to_drive(custom_path=file_path)

    # 7.3. Analyze file via Gemini (Placeholder logic)
    # In a real scenario, you might have an image-to-text model or something similar.
    # For now, we'll do a simple "prompt" to Gemini describing we have a file with certain name.
    try:
        prompt_text = f"Describe the file named: {file_path}."
        palm_response = palm.generate_text(
            model="models/text-bison-001",
            prompt=prompt_text
        )
        description = palm_response.result if palm_response else "No description from Gemini."
    except Exception as e:
        logger.exception("Error calling Gemini API")
        description = "Could not describe the file."

    # 7.4. Save file metadata to DB
    file_doc = {
        "chat_id": chat_id,
        "file_id": file_id,
        "file_name": file_path,
        "file_type": file_type,
        "description": description,
        "timestamp": datetime.datetime.utcnow()
    }
    db.files.insert_one(file_doc)

    # 7.5. Reply to user
    await update.message.reply_text(
        f"File '{file_path}' analysis:\n{description}"
    )

# -----------------------------------------------------------------------------
# 8. Web Search Command (/websearch)
# -----------------------------------------------------------------------------
async def websearch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /websearch command.
       Usage: /websearch <search query>
    """
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("Usage: /websearch <search query>")
        return

    query = " ".join(args)

    # 8.1. Perform the web search (placeholder logic).
    #      Replace with actual search API or AI agent that can search the web.
    try:
        search_results = await perform_web_search(query)
        # Summarize with Gemini
        summary = await summarize_results_with_gemini(query, search_results)
    except Exception as e:
        logger.exception("Error with web search")
        await update.message.reply_text("Error performing web search.")
        return

    # 8.2. Format the response
    response_text = f"**Summary**:\n{summary}\n\n**Top Links**:\n"
    for i, link in enumerate(search_results[:5], 1):
        response_text += f"{i}. {link}\n"

    # 8.3. Save to MongoDB
    search_doc = {
        "chat_id": chat_id,
        "query": query,
        "summary": summary,
        "links": search_results[:5],
        "timestamp": datetime.datetime.utcnow()
    }
    db.websearch.insert_one(search_doc)

    # 8.4. Send the result
    await update.message.reply_text(response_text, parse_mode="Markdown")

# -----------------------------------------------------------------------------
# 9. Helper Functions for Web Search & Summarization
# -----------------------------------------------------------------------------
async def perform_web_search(query: str):
    """Perform a web search and return a list of top result URLs.
       Replace with your actual search logic or an external API.
    """
    # Example of a naive placeholder that returns dummy links
    # In real usage, you'd call some search engine API or similar.
    # e.g., use Bing API, Google Custom Search, etc.
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
    except Exception as e:
        logger.exception("Error calling Gemini for summary")
        return "No summary available"

# -----------------------------------------------------------------------------
# 10. Main Function: Set up Handlers & Start Bot
# -----------------------------------------------------------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("websearch", websearch_handler))

    # Contact handler (phone sharing)
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # File handlers (images, documents)
    file_filter = (filters.Document.ALL | filters.PHOTO)
    application.add_handler(MessageHandler(file_filter, file_message_handler))

    # Text message handler (fallback for everything else that is text)
    text_filter = filters.TEXT & (~filters.COMMAND)
    application.add_handler(MessageHandler(text_filter, text_message_handler))

    # Start polling
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
```

---

## How This Code Works

1. **Registration (`/start`)**  
   - When a user starts the bot:
     - We insert their info (`chat_id`, `username`, etc.) into the `users` collection if not already registered.
     - We request the user’s phone number by sending a **Contact** button (Telegram feature).

2. **Storing the Phone Number**  
   - A **MessageHandler** with `filters.CONTACT` updates the user document in MongoDB with the phone number when shared.

3. **Gemini-Powered Chat**  
   - For any **text message** (that isn’t a command), we:
     1. Save the user’s message in `messages` collection.
     2. Send it to Gemini (`palm.generate_text`) to get a response.
     3. Store the AI response in the DB.
     4. Reply back to the user.

4. **Image/File Analysis**  
   - We capture **photo** or **document** uploads with a file filter.
   - Download the file (optional) and store locally for demonstration.
   - Send a prompt to Gemini describing the file to get a “description.”
   - Save metadata in the `files` collection (`filename`, `description`, timestamps).
   - Reply to the user with the analysis result.

5. **Web Search**  
   - `/websearch <query>` triggers an async search function (`perform_web_search`).
   - Summarize the top links with Gemini.
   - Store the query, summary, and links in the `websearch` collection.
   - Send the summary + links back to the user.

---

### Next Steps & Tips

- **Security**: Always store API keys and database credentials in environment variables or a secure location.
- **Scalability**: 
  - Dockerize your app and consider a scalable service (e.g., AWS ECS, Heroku) for deployment.
  - Use a cloud MongoDB service (like MongoDB Atlas).
- **Error Handling**: Add comprehensive try/except blocks and user-friendly error messages.
- **Referrals & Analytics**: 
  - For a referral system, track invites in your `users` collection (e.g., store who invited whom).
  - For analytics, you can build a small web dashboard in Flask/Node.js that displays charts from `users`, `messages`, `files`, etc.
- **Translations & Sentiment**:
  - Integrate libraries (e.g., `googletrans` for quick translations) or more advanced NLP services for sentiment analysis.

Feel free to adapt and expand on this base code to implement your desired features. Good luck building your Telegram AI Chatbot!
