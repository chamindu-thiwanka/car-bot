from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

app = Flask(__name__)

# Google Sheets API Setup
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u30X8HFuRqWhPYK2ox3I5uU4ixgl9S09SQ6oA5-IdK4/edit#gid=1287662998"
SHEET_NAME = "Sheet2"  # Change this if your sheet name is different

# Authenticate and open Google Sheet

load_dotenv()  # Load environment variables

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if not GOOGLE_CREDENTIALS_JSON:
    raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON is not set!")

creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)

# List of allowed phone numbers (Include full international format: e.g., +94712345678)
ALLOWED_NUMBERS = {"whatsapp:+94763243006", "whatsapp:+94767878595"}
NOT_ALLOWED_NUMBERS = {"whatsapp:+94760000000", "whatsapp:+94760000000"}  # Add more numbers if needed

@app.route("/", methods=["POST"])
def bot():
    user_msg = request.values.get('Body', '').strip().lower()
    sender_number = request.values.get('From', '').strip()  # Get sender's WhatsApp number

    # Log the incoming request details in the terminal
    print(f"📩 Incoming WhatsApp message:")
    print(f"   - From: {sender_number}")
    print(f"   - Message: {user_msg}")

    response = MessagingResponse()

    # Check if sender is in the allowed list
    if sender_number not in ALLOWED_NUMBERS:
        response.message("❌ *Access Denied!*\nYou are not authorized to use this service.")
        return str(response)

    # Fetch data from the Google Sheet
    data = sheet.get_all_values()
    headers = data[0]  # First row as headers
    records = data[1:]  # Rest of the rows as records

    # Search for matching words in the title
    matched_records = []
    for row in records:
        title = row[0].strip().lower()
        if user_msg in title:  # Partial match instead of exact match
            matched_records.append(row)

    # Prepare response
    if matched_records:
        msg_body = "🔍 *Search Results:*\n\n"
        for record in matched_records[:10]:  # Limit to 5 results for readability
            msg_body += (
                f"🚗 *{record[0]}*\n"
                f"💰 {record[1]}\n"
                f"📍 {record[2]}\n"
                f"📏 {record[3]}\n"
                f"🔗 [Listing]({record[4]})\n\n"
            )
    else:
        msg_body = f"❌ No records found for '{user_msg}'. Please try another search."

    response.message(msg_body)
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)
