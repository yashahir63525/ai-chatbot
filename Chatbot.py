# === INSTALLS (Only run once) ===
# Run this as a separate script or manually install these in local environment:
# pip install pytesseract pillow PyPDF2 python-docx openai serpapi gspread oauth2client

# Run first if this is first time this command "pip install -r requirements.txt"

import os
import json
import pytesseract
import PIL.Image
import PyPDF2
import docx
import gspread
from datetime import datetime
from openai import OpenAI
from serpapi import GoogleSearch
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()  # Load .env vars


service_account_info = {
    "type": os.getenv("GCP_TYPE"),
    "project_id": os.getenv("GCP_PROJECT_ID"),
    "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GCP_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GCP_CLIENT_EMAIL"),
    "client_id": os.getenv("GCP_CLIENT_ID"),
    "auth_uri": os.getenv("GCP_AUTH_URI"),
    "token_uri": os.getenv("GCP_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL"),
}

creds = Credentials.from_service_account_info(service_account_info)
gc = gspread.authorize(creds)

# === Setup Google Sheets ===
cred_file = "chatbot-467212-076f56c6938b.json"
if not os.path.exists(cred_file):
    print("❌ Please place your service account JSON key named:", cred_file)
    exit()

try:
    gc = gspread.service_account(filename=cred_file)
    sheet_name = "Chatbotbhai Logs"
    sh = gc.open(sheet_name)
    worksheet = sh.sheet1

    if not worksheet.get_all_values():
        worksheet.append_row(["Timestamp", "User", "Chatbotbhai"])

except Exception as e:
    with open(cred_file) as f:
        data = json.load(f)
    print("❌ Google Auth Error. Share this email with edit access to your Sheet:")
    print(f"🔑 {data['client_email']}")
    raise e

# === Setup OpenRouter ===
client = OpenAI(
    base_url=os.getenv("OPENAPI_BASE_URL"),
    api_key=os.getenv("OPENAPI_API_KEY"),
)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
mode = "chat"
file_content = ""
chat_history = []

def log_to_sheet(user_msg, bot_msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worksheet.append_row([timestamp, user_msg, bot_msg])

print("📢 Welcome to Chatbotbhai (Enhanced Edition)")
print("📝 Type your message")
print("📁 Type `File` to upload documents")
print("🖼️ Type `Image` to upload an image for OCR")
print("🌐 Type `Online` for real-time web search")
print("💬 Type `Chatting` to return to normal chat")
print("🗂️ Type `Log Sheet Download` to download logs")
print("🚪 Type `Exit` to quit\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("Chatbotbhai: Goodbye! 👋")
        break

    elif user_input.lower() == "file":
        print("Chatbotbhai: Please enter the file path (PDF/DOCX/TXT):")
        file_path = input("Path: ").strip()
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
            elif ext == ".pdf":
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    file_content = "\n".join([page.extract_text() or "" for page in reader.pages])
            elif ext == ".docx":
                doc = docx.Document(file_path)
                file_content = "\n".join([para.text for para in doc.paragraphs])
            else:
                print("Chatbotbhai: ❌ Unsupported file format.")
                continue
            print("Chatbotbhai: ✅ File loaded! Ask your question.")
            mode = "file"
            continue
        except Exception as e:
            print("Chatbotbhai: ❌ Failed to load file:", e)
            continue

    elif user_input.lower() == "image":
        print("Chatbotbhai: Enter the image path (PNG/JPG):")
        img_path = input("Path: ").strip()
        try:
            img = PIL.Image.open(img_path)
            file_content = pytesseract.image_to_string(img)
            print("Chatbotbhai: ✅ Text extracted from image. Ask your question.")
            mode = "image"
            continue
        except Exception as e:
            print("Chatbotbhai: ❌ OCR failed:", e)
            continue

    elif user_input.lower() == "online":
        mode = "online"
        print("🌐 Enter your query (type 'exitonline' to return):")
        continue

    elif user_input.lower() == "exitonline":
        mode = "chat"
        print("Chatbotbhai: ✅ Back to chat mode.")
        continue

    elif user_input.lower() == "chatting":
        mode = "chat"
        print("Chatbotbhai: ✅ Chat mode resumed.")
        continue

    elif user_input.lower() == "log sheet download":
        print("📥 Chatbotbhai: Here's your log download link:")
        print(f"https://docs.google.com/spreadsheets/d/{sh.id}/export?format=xlsx")
        continue

    # === Prompt Creation ===
    if mode in ["file", "image"]:
        prompt = f"Based on the following content, answer the question:\n\n{file_content}\n\nQuestion: {user_input}"
        messages = [{"role": "user", "content": prompt}]
    elif mode == "online":
        try:
            print("Chatbotbhai 🌐: Searching...")
            search = GoogleSearch({
                "q": user_input,
                "location": "India",
                "hl": "en",
                "gl": "in",
                "api_key": SERPAPI_KEY
            })
            results = search.get_dict()
            snippets = "\n".join([r["snippet"] for r in results.get("organic_results", []) if "snippet" in r][:5])
            prompt = f"User Question: {user_input}\n\nSearch Results:\n{snippets}\n\nAnswer:"
            messages = [{"role": "user", "content": prompt}]
        except Exception as e:
            print(f"❌ Online search failed: {e}")
            continue
    else:
        chat_history.append({"role": "user", "content": user_input})
        messages = chat_history[-10:]

    # === Generate response ===
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=messages
        )
        reply = response.choices[0].message.content
        print(f"Chatbotbhai: {reply}")
        if mode == "chat":
            chat_history.append({"role": "assistant", "content": reply})
        log_to_sheet(user_input, reply)
    except Exception as e:
        print("❌ Chat failed:", e)
