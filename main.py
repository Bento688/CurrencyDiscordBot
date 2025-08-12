import discord
import os
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

API_KEY = os.getenv('API_KEY')
API_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair'
CHANNEL_ID = os.getenv('CHANNEL_ID')
ACTIVE_HOURS = range(9, 23) #Set the time range of the auto-message

#Feth conversion rate data
def fetch_rate(base, target):
    response = requests.get(API_URL + f"/{base}" + f"/{target}")
    data = response.json()
    return data["conversion_rate"]

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    client.loop.create_task(send_rate_on_the_hour())

#Handling $rate commands  
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$rate'):
        parts = message.content.split()
        
        # Case 1: No currencies → default TWD to IDR
        if len(parts) == 1:
            base, target = "TWD", "IDR"
        # Case 2: Two currencies provided
        elif len(parts) == 3:
            base, target = parts[1].upper(), parts[2].upper()
        else:
            await message.channel.send("⚠️ Usage: `$rate [BASE] [TARGET]` (e.g., `$rate USD JPY`)")
            return
        
        try:
            rate = fetch_rate(base, target)
            if rate:
                await message.channel.send(f"💱 1 {base} = {rate:,.2f} {target}")
            else:
                await message.channel.send(f"⚠️ Could not fetch rate for {base} → {target}. Check currency codes.")
        except Exception as e:
            await message.channel.send("⚠️ Error fetching exchange rate.")
            print("Error:", e)


# Send TWD rate every HH:00
async def send_rate_on_the_hour():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    
    while not client.is_closed():
        now = datetime.now()
        # Calculate seconds until the next :00
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        
        # Check active hours
        current_hour = datetime.now().hour
        if current_hour in ACTIVE_HOURS:
            try:
                rate = await asyncio.to_thread(fetch_rate, "TWD", "IDR")
                if rate:
                    await channel.send(f"💱 1 NTD = {rate:,.2f} IDR")     
            except Exception as e:
                print("Error sending hourly rate:", e)
   
client.run(os.getenv('TOKEN'))