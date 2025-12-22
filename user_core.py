from telethon import TelegramClient, events, functions, types
import asyncio, os, time, pytz
from datetime import datetime

# الأرقام المزخرفة للساعة
fonts = {"0":"𝟘","1":"𝟙","2":"𝟚","3":"𝟛","4":"𝟜","5":"𝟝","6":"𝟞","7":"𝟟","8":"𝟠","9":"𝟡",":":":","A":"𝔸","P":"ℙ","M":"𝕄"}
def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

async def start_user_source(session_path, api_id, api_hash):
    client = TelegramClient(session_path, api_id, api_hash)
    save_enabled = True
    storage_id = None
    name_task = None # لتخزين مهمة تشغيل الوقت
    DEV_USER = "@I_QQ_Q"
    SOURCE_CH = "@SORS_RECO"

    # ميزة تحديث الوقت في الاسم
    async def auto_update_name():
        while True:
            try:
                tz = pytz.timezone('Asia/Baghdad')
                t_str = datetime.now(tz).strftime("%I:%M %p")
                styled_t = get_styled_time(t_str)
                await client(functions.account.UpdateProfileRequest(first_name=f"RECO | {styled_t}"))
                await asyncio.sleep(60)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(10)

    async def setup_storage():
        nonlocal storage_id
        async for dialog in client.iter_dialogs():
            if dialog.is_group and dialog.name == "RECO STORAGE":
                storage_id = dialog.id; return
        res = await client(functions.messages.CreateChatRequest(title="RECO STORAGE", users=["me"]))
        storage_id = res.chats[0].id

    @client.on(events.NewMessage)
    async def main_handler(event):
        nonlocal save_enabled, name_task
        if event.out:
            if event.raw_text == ".فحص":
                start_t = time.time()
                me = await client.get_me()
                tz = pytz.timezone('Asia/Baghdad')
                time_now = datetime.now(tz).strftime("%I:%M:%S %p")
                ping = round((time.time() - start_t) * 1000, 2)
                check_text = (
                    f"🛡 **تـقـريـر فـحـص سـورس ريـكـو :**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👤 **صاحب السورس :** {me.first_name}\n"
                    f"🆔 **ايدي الحساب :** `{me.id}`\n"
                    f"📡 **سـرعـة الـبـنـج :** `{ping}ms`\n"
                    f"⏰ **الـوقـت (بغداد) :** `{time_now}`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👨‍💻 **المطور :** {DEV_USER}\n"
                    f"🦅 **- RECO SOURCE IS ACTIVE -**"
                )
                try:
                    await client.send_message(event.chat_id, check_text, file=f"https://t.me/SORS_RECO/4")
                    await event.delete()
                except: await event.edit(check_text)

            elif event.raw_text == ".الاوامر":
                help_text = (
                    f"👑 **قـائـمـة تـحـكـم سـورس ريـكـو**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🔹 `.فحص` : فحص السورس.\n"
                    f"🔹 `.ذاتيه` : تفعيل حفظ الذاتية.\n"
                    f"🔹 `.تعطيل الذاتيه` : إيقاف الحفظ.\n"
                    f"🔹 `.وقت_تشغيل` : تفعيل الساعة بالاسم.\n"
                    f"🔹 `.وقت_إطفاء` : إيقاف ساعة الاسم.\n"
                    f"🔹 `.ايدي` : عرض ايديك.\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👨‍💻 **Dev:** {DEV_USER} | **CH:** {SOURCE_CH}"
                )
                await event.edit(help_text)

            elif event.raw_text == ".وقت_تشغيل":
                if not name_task or name_task.done():
                    name_task = asyncio.create_task(auto_update_name())
                    await event.edit(f"✨ **تم تفعيل ساعة الاسم بنجاح.**\n👤 بواسطة: {DEV_USER}")
                else: await event.edit("⚠️ الساعة تعمل بالفعل.")

            elif event.raw_text == ".وقت_إطفاء":
                if name_task:
                    name_task.cancel(); name_task = None
                    await client(functions.account.UpdateProfileRequest(first_name="RECO"))
                    await event.edit("📴 **تم إيقاف ساعة الاسم.**")

            elif event.raw_text == ".ذاتيه":
                save_enabled = True
                await event.edit(f"✅ **تم تفعيل حفظ الذاتية.**\n🦅 {SOURCE_CH}")

        if not event.out and event.is_private:
            if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds and save_enabled:
                path = await event.download_media()
                cap = f"📥 **اقتناص ميديا ذاتية التدمير**\n👤 من: `{event.sender_id}`\n👨‍💻 مطور السورس: {DEV_USER}"
                await client.send_message("me", cap, file=path)
                if storage_id: await client.send_message(storage_id, cap, file=path)
                os.remove(path)
            elif storage_id and not getattr((await event.get_sender()), 'bot', False):
                await client.forward_messages(storage_id, event.message)

    await client.start()
    await setup_storage()
    await client.run_until_disconnected()
