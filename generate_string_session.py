# @title <center>𝙏𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙐𝙨𝙚𝙧𝙎𝙚𝙨𝙨𝙞𝙤𝙣</center>

from pyrogram import Client
from pyrogram.errors import UserIsBot
import asyncio

API_KEY = ""  # Replace with your actual API key
API_HASH = ""  # Replace with your actual API hash
header = "Your Header"  # Replace with your actual header text

async def generate_session_string():
    async with Client(name="SurfTG-User", api_id=API_KEY, api_hash=API_HASH, in_memory=True) as app:
        sess = await app.export_session_string()
        print("\nGenerating ...")
        donestr = "Sent to Saved Messages!!"
        try:
            await app.send_message("me", f"#SurfTG {header}\n\n<code>{sess}</code>")
        except UserIsBot:
            donestr = "Successfully Printed !!"
            print(f"#SurfTG {header}")
            print(sess)
        print(f"Done !!, String Session has been {donestr}")

asyncio.run(generate_session_string())

