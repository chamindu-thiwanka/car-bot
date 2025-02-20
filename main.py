from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets API Setup
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u30X8HFuRqWhPYK2ox3I5uU4ixgl9S09SQ6oA5-IdK4/edit#gid=1287662998"
SHEET_NAME = "Sheet2"  # Change this if your sheet name is different

# Authenticate and open Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("ikmanscrapertosheets-e987f101b56c.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)

@app.route("/", methods=["POST"])
def bot():
    user_msg = request.values.get('Body', '').strip().lower()
    response = MessagingResponse()
    
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
        for record in matched_records[:5]:  # Limit to 5 results for readability
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
