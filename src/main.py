import discord
from discord import app_commands
import gspread
from google.oauth2.service_account import Credentials
from commands.set_payment_command import register_set_payment_command

# Load the bot token from token.txt
with open('token.txt', 'r') as file:
    TOKEN = file.read().strip()

# Load the spreadsheet ID from spreadsheet_id.txt
with open('spreadsheet_id.txt', 'r') as file:
    spreadsheet_id = file.read().strip()

# Define the Google Sheets API scope and authorize access
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("key.json", scopes=SCOPE)
client_sheets = gspread.authorize(creds)

# Open the spreadsheet by ID
spreadsheet = client_sheets.open_by_key(spreadsheet_id)

# Discord bot setup
intents = discord.Intents.default()

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        try:
            # Register all commands
            await register_set_payment_command(self, spreadsheet)

            await self.tree.sync()
            print("Slash commands synced successfully")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

client = MyClient()

# Run the bot
client.run(TOKEN)
