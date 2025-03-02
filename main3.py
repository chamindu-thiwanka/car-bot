from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Load environment variables
load_dotenv()

def create_keyfile_dict():
    variables_keys = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("UNIVERSE_DOMAIN")
    }
    return variables_keys

# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(create_keyfile_dict(), scope)
    client = gspread.authorize(creds)
except Exception as e:
    raise ValueError(f"❌ Google Sheets Authentication Failed: {e}")

# Google Sheets API Setup
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u30X8HFuRqWhPYK2ox3I5uU4ixgl9S09SQ6oA5-IdK4/edit#gid=1287662998"
SHEET_NAME = "Sheet2"  # Change this if your sheet name is different

try:
    sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
except Exception as e:
    raise ValueError(f"❌ Error accessing Google Sheet: {e}")

# Allowed and blocked WhatsApp numbers (use full international format)
ALLOWED_NUMBERS = {"whatsapp:+94763243006", "whatsapp:+94767878595"}
BLOCKED_NUMBERS = {"whatsapp:+94760000000"}

@app.route("/", methods=["POST"])
def bot():
    user_input = request.values.get('Body', '').strip()
    user_msg = user_input.lower()  # Convert to lowercase for case-insensitive search
    sender_number = request.values.get('From', '').strip()  # Get sender's WhatsApp number

    # Log the incoming request details in the terminal
    print(f"📩 Incoming WhatsApp message:")
    print(f"   - From: {sender_number}")
    print(f"   - Message: {user_input} (Normalized: {user_msg})")

    response = MessagingResponse()

    # Check if sender is in the allowed list
    if sender_number in BLOCKED_NUMBERS:
        response.message("🚫 *You are blocked from using this service.*")
        return str(response)

    if sender_number not in ALLOWED_NUMBERS:
        response.message("❌ *Access Denied!*\nYou are not authorized to use this service.")
        return str(response)

    try:
        # Fetch data from Google Sheet
        data = sheet.get_all_values()
        headers = data[0]  # First row as headers
        records = data[1:]  # Rest of the rows as records

        # Search for matching words in the title (column 0) - case insensitive
        matched_records = [
            row for row in records if user_msg in row[0].strip().lower()
        ]

        # Function to split long messages into chunks
        def split_message(message, limit=1500):
            chunks = []
            while len(message) > limit:
                # Find a safe split point (end of a record)
                split_index = message.rfind('\n\n', 0, limit)
                if split_index == -1:  # Fallback if no split point is found
                    split_index = limit
                chunks.append(message[:split_index])
                message = message[split_index:].strip()
            chunks.append(message)
            return chunks
        
        # Prepare response
        if matched_records:
            msg_body = f"🔍 *Search Results for '{user_input}':*\n\n"
            for record in matched_records[:20]:  # Adjust the number of records as needed
                msg_body += (
                    f"🚗 *{record[0]}*\n"
                    f"💰 Price: {record[1]}\n"
                    f"📍 Location: {record[2]}\n"
                    f"📏 Mileage: {record[3]}\n"
                    f"📆 Ad Created Date: {record[6]}\n"
                    f"🔗 [Listing]({record[4]})\n\n"
                )
        
            # Split and send messages in chunks
            message_chunks = split_message(msg_body)
            for i, chunk in enumerate(message_chunks):
                # If there are multiple chunks, add indicators
                if len(message_chunks) > 1:
                    chunk = f"{chunk}\n[Part {i+1}/{len(message_chunks)}]"
                response.message(chunk)
        else:
            response.message(f"❌ No records found for '{user_input}'. Please try another search.")

    except Exception as e:
        print(f"Error processing request: {e}")
        response.message(f"⚠️ An error occurred: {str(e)}")

    return str(response)

if __name__ == "__main__":
    app.run(debug=True)
