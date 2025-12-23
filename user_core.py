from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
import asyncio, os, time, pytz
from datetime import datetime

# الأرقام المزخرفة للساعة
fonts = {"0":"𝟘","1":"𝟙","2":"𝟚","3":"𝟛","4":"𝟜","5":"𝟝","6":"𝟞","7":"𝟟","8":"𝟠","9":"𝟡",":":":","A":"𝔸","P":"ℙ","M":"𝕄"}
def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

async def start_user_source(session_str, api_id, api_hash, install_info=None):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    save_enabled = True
    storage_id = None
    name_task = None 
    original_name = "" # لحفظ اسم المستخدم الأصلي
    DEV_USER = "@I_QQ_Q"
    SOURCE_CH = "@SORS_RECO"
    start_time = datetime.now()

    # ميزة تحديث الوقت بجانب اسم المستخدم الأصلي
    async def auto_update_name():
        nonlocal original_name
        try:
            me = await client.get_me()
            # حفظ الاسم الأول فقط إذا لم يكن محفوظاً لتجنب تكرار الوقت في الاسم
            original_name = me.first_name.split('|')[0].strip()
        except: original_name = "User"

        while True:
            try:
                tz = pytz.timezone('Asia/Baghdad')
                t_str = datetime.now(tz).strftime("%I:%M %p")
                styled_t = get_styled_time(t_str)
                # دمج اسم المستخدم الأصلي مع الوقت المزين
                await client(functions.account.UpdateProfileRequest(first_name=f"{original_name} | {styled_t}"))
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
                    f"🛡 **تـقـريـر فـحـص سـورس ريـكـو الـفـخـم :**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👑 **الـمـسـتـخـدم :** [{me.first_name}](tg://user?id={me.id})\n"
                    f"🆔 **الايـدي :** `{me.id}`\n"
                    f"📡 **سـرعـة الاسـتـجـابـة :** `{ping}ms`\n"
                    f"⏰ **الـوقـت الـحـالـي :** `{time_now}`\n"
                    f"⚙️ **الـحـالـة :** `ACTIVE ✅`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE IS THE BEST -**\n"
                    f"👨‍💻 **Dev:** {DEV_USER} | **Channel:** {SOURCE_CH}"
                )
                try:
                    await client.send_message(event.chat_id, check_text, file=f"https://t.me/SORS_RECO/4")
                    await event.delete()
                except: await event.edit(check_text)

            elif event.raw_text == ".الاوامر":
                help_text = (
                    f"⚜️ **قـائـمـة تـحـكـم سـورس ريـكـو الـعـالـمـي** ⚜️\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🚀 `.فحص` : لـمـعـرفـة حـالـة الـسـورس.\n"
                    f"📸 `.ذاتيه` : تـفـعـيـل حـفـظ الـمـيـديـا الـمـخـفـيـة.\n"
                    f"🚫 `.تعطيل ذاتيه` : إيـقـاف حـفـظ الـمـيـديـا.\n"
                    f"🕒 `.وقت_تشغيل` : تـفـعـيـل الـسـاعـة بـجـانـب اسـمـك.\n"
                    f"📴 `.وقت_إطفاء` : إيـقـاف الـسـاعـة الـتـلـقـائـيـة.\n"
                    f"👤 `.ايدي` | `.معلوماتي` : كـشـف بـيـانـات الـتـنـصـيـب.\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🔗 **Channel:** @SORS_RECO\n"
                    f"👤 **Developer:** @I_QQ_Q\n"
                    f"🦅 **- RECO SOURCE STRENGTH -**"
                )
                await event.edit(help_text)

            elif event.raw_text in [".ايدي", ".معلوماتي"]:
                me = await client.get_me()
                full = await client(functions.users.GetFullUserRequest(me.id))
                bio = full.full_user.about or "لا يوجد نبذة تعريفية"
                uptime = datetime.now() - start_time
                days, remainder = divmod(uptime.seconds + (uptime.days * 86400), 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, _ = divmod(remainder, 60)
                
                inst_date = install_info.get('date', 'غير متوفر') if install_info else "غير متوفر"
                
                info_text = (
                    f"💎 **مـعـلومـات الـعـضـويـة والـتـنـصـيـب :**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👤 **الاسـم :** {me.first_name}\n"
                    f"🆔 **الايـدي :** `{me.id}`\n"
                    f"🔗 **الـيـوزر :** @{me.username if me.username else 'None'}\n"
                    f"📝 **الـبـايـو :** `{bio}`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"📅 **تـاريـخ الـتـنـصـيـب :** `{inst_date}`\n"
                    f"⏱ **مـدة الـعـمـل :** `{hours} ساعة و {minutes} دقيقة`\n"
                    f"📡 **الـسـيـرفـر :** `Cloud Active ✅`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **Dev:** {DEV_USER} | **CH:** {SOURCE_CH}"
                )
                photos = await client.get_profile_photos("me")
                if photos:
                    await client.send_message(event.chat_id, info_text, file=photos[0])
                    await event.delete()
                else: await event.edit(info_text)

            elif event.raw_text == ".وقت_تشغيل":
                if not name_task or name_task.done():
                    name_task = asyncio.create_task(auto_update_name())
                    await event.edit(f"✅ **تـم تـفـعـيـل سـاعـة الاسـم الـتـلـقـائـيـة.**\n💡 الـسـاعـة الآن تـظـهـر بـجـانـب اسـمـك الـحـقـيـقـي.")
                else: await event.edit("⚠️ الـسـاعـة تـعـمـل بـالـفـعـل.")

            elif event.raw_text == ".وقت_إطفاء":
                if name_task:
                    name_task.cancel(); name_task = None
                    # استعادة الاسم الأصلي بدون وقت
                    await client(functions.account.UpdateProfileRequest(first_name=original_name))
                    await event.edit("📴 **تـم إيـقـاف سـاعـة الاسـم واسـتـعـادة اسـمـك الأصـلـي.**")

            elif event.raw_text == ".ذاتيه":
                save_enabled = True
                await event.edit(f"✅ **تـم تـفـعـيـل اقـتـنـاص الـذاتـيـة بـنـجـاح.**")

            elif event.raw_text == ".تعطيل ذاتيه":
                save_enabled = False
                await event.edit(f"❌ **تـم تـعـطـيـل اقـتـنـاص الـذاتـيـة.**")

        if not event.out and event.is_private:
            if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds and save_enabled:
                path = await event.download_media()
                cap = f"📥 **تـم اقـتـنـاص مـيـديـا ذاتـيـة الـتـدمـيـر !**\n👤 **الـمـرسـل :** `{event.sender_id}`\n⏰ **الـوقـت :** {datetime.now().strftime('%H:%M')}\n‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n🦅 **RECO SOURCE**"
                await client.send_message("me", cap, file=path)
                if storage_id: await client.send_message(storage_id, cap, file=path)
                os.remove(path)
            elif storage_id and not getattr((await event.get_sender()), 'bot', False):
                await client.forward_messages(storage_id, event.message)

    await client.start()
    await setup_storage()
    await client.run_until_disconnected()
