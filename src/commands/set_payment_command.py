import asyncio
import discord
from discord import app_commands
from datetime import datetime
import pytz
from roobetDiscordBot.src.rate_limiter import process_request_with_retry, is_on_cooldown, update_cooldown

async def register_set_payment_command(bot, sheet):
    # Retrieve payment options from the first row of the spreadsheet (excluding columns A and B)
    payment_sheet = sheet.worksheet("users_payment_information")
    payment_options = await asyncio.to_thread(payment_sheet.row_values, 1)
    valid_payment_options = payment_options[2:]  # Skipping columns A and B

    # Prepare choices for app_commands
    choices = [app_commands.Choice(name=opt, value=opt) for opt in valid_payment_options]

    @bot.tree.command(name="setpayment", description="Set your preferred payment method")
    @app_commands.describe(
        payment_option="Choose a payment option",
        payment_info="Provide the relevant information for the chosen payment option"
    )
    @app_commands.choices(payment_option=choices)
    async def setpayment(interaction: discord.Interaction, payment_option: app_commands.Choice[str], payment_info: str):
        # Check if the user is on cooldown
        if is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "You're on cooldown. Please wait before making another request.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)  # Defer the response to avoid timeout

        discord_user_id = str(interaction.user.id)
        discord_username = str(interaction.user)

        # Fetch existing Discord IDs from column A
        discord_ids = await asyncio.to_thread(payment_sheet.col_values, 1)

        # Check if the user exists in the sheet, or create a new entry
        if discord_user_id in discord_ids:
            row = discord_ids.index(discord_user_id) + 1  # Get the existing row
        else:
            row = len(discord_ids) + 1  # Create a new entry in the next available row
            await process_request_with_retry(payment_sheet.update, f'A{row}', [[discord_user_id]])
            await process_request_with_retry(payment_sheet.update, f'B{row}', [[discord_username]])

        # Determine the column to update based on the chosen payment option
        selected_option = payment_option.value
        column_index = valid_payment_options.index(selected_option) + 3  # +3 because A, B, and 1-based index
        column_letter = chr(64 + column_index)  # Convert to column letter (e.g., 3 -> 'C')
        message = f"Your {selected_option} information has been set to: {payment_info}"

        # Update the relevant column with the provided payment info
        await process_request_with_retry(payment_sheet.update, f'{column_letter}{row}', [[payment_info]])

        # Confirm the update and set cooldown
        await interaction.followup.send(message, ephemeral=True)
        update_cooldown(interaction.user.id)
