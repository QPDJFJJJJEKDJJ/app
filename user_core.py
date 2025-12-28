from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import CreateChatRequest
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio, os, time, pytz
from datetime import datetime, timedelta

# --- الأرقام والخطوط المزخرفة المطورة لـ سورس ريكو ---
fonts = {
    "0":"𝟘",
    "1":"𝟙",
    "2":"𝟚",
    "3":"𝟛",
    "4":"𝟜",
    "5":"𝟝",
    "6":"𝟞",
    "7":"𝟟",
    "8":"𝟠",
    "9":"𝟡",
    ":":":",
    "A":"𝔸",
    "P":"ℙ",
    "M":"𝕄"
}

def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

async def start_user_source(session_str, api_id, api_hash, install_info=None):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    
    # --- متغيرات التحكم الأساسية ---
    save_enabled = True
    bold_enabled = False 
    storage_pv = None    
    storage_groups = None 
    storage_deleted = None 
    name_task = None 
    original_name = "" 
    DEV_USER = "@I_QQ_Q"
    SOURCE_CH = "SORS_RECO"
    
    # قائمة الإدمنية المرفوعين بالبوت
    admins_list = []
    
    # مخزن الرسائل المحذوفة (الكاش) لضمان الاستعادة
    msg_cache = {}

    # --- وظيفة تحديث الوقت في الاسم تلقائياً ---
    async def auto_update_name():
        nonlocal original_name
        try:
            me = await client.get_me()
            if not original_name or "|" in original_name:
                original_name = me.first_name.split('|')[0].strip()
        except: 
            original_name = "User"

        while True:
            try:
                tz = pytz.timezone('Asia/Baghdad')
                time_now_str = datetime.now(tz).strftime("%I:%M %p")
                styled_time = get_styled_time(time_now_str)
                await client(functions.account.UpdateProfileRequest(
                    first_name=f"{original_name} | {styled_time}"
                ))
                await asyncio.sleep(60) 
            except asyncio.CancelledError: 
                break
            except Exception: 
                await asyncio.sleep(10)

    # --- وظيفة إنشاء وجلب أيدي التخزين ---
    async def create_and_get_id(title):
        try:
            async for dialog in client.iter_dialogs(limit=50):
                if dialog.name == title: 
                    return dialog.id
            
            result = await client(CreateChatRequest(title=title, users=["me"]))
            return result.chats[0].id
        except:
            return None

    # --- إعداد القنوات ومجموعات التخزين عند التشغيل ---
    async def setup_all_storages():
        nonlocal storage_pv, storage_groups, storage_deleted
        try: 
            await client(JoinChannelRequest(SOURCE_CH))
        except: 
            pass

        async for dialog in client.iter_dialogs(limit=100):
            if dialog.name == "RECO PV STORAGE": 
                storage_pv = dialog.id
            elif dialog.name == "RECO GROUPS STORAGE": 
                storage_groups = dialog.id
            elif dialog.name == "RECO DELETED STORAGE": 
                storage_deleted = dialog.id
        
        if not storage_pv: 
            storage_pv = await create_and_get_id("RECO PV STORAGE")
        if not storage_groups: 
            storage_groups = await create_and_get_id("RECO GROUPS STORAGE")
        if not storage_deleted: 
            storage_deleted = await create_and_get_id("RECO DELETED STORAGE")

    # --- تنظيف الكاش بشكل دوري للرسائل القديمة ---
    async def cache_cleaner():
        while True:
            await asyncio.sleep(60)
            now = datetime.now()
            to_delete = [m_id for m_id, data in msg_cache.items() if now > data['expiry']]
            for m_id in to_delete:
                msg_cache.pop(m_id, None)

    # --- معالج الرسائل الجديد (المطور) ---
    @client.on(events.NewMessage)
    async def main_handler(event):
        nonlocal save_enabled, name_task, original_name, bold_enabled, admins_list
        
        sender_id = event.sender_id
        me = await client.get_me()
        my_id = me.id
        
        # التحقق من الرتبة (هل هو المالك أو إدمن مساعد)
        is_admin = (sender_id == my_id) or (sender_id in admins_list)

        # تخزين الرسائل الواردة لغرض كشف المحذوفات
        if event.is_private and not event.out:
            msg_cache[event.id] = {
                'message': event.message,
                'expiry': datetime.now() + timedelta(minutes=10)
            }

        # --- معالجة الأوامر (تستجيب للمالك وللإدمن المرفوع) ---
        if is_admin:
            cmd = event.raw_text

            # أمر رفع إدمن (للمالك فقط) - تم البدء بـ IF لتفادي الخطأ
            if cmd.startswith(".ادمن") and sender_id == my_id:
                user_to_add = None
                if event.is_reply:
                    reply_msg = await event.get_reply_message()
                    user_to_add = reply_msg.sender_id
                else:
                    parts = cmd.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        user_to_add = int(parts[1])
                
                if user_to_add:
                    if user_to_add not in admins_list:
                        admins_list.append(user_to_add)
                        await event.edit(f"✅ **تـم رفـع الـمـسـتـخدم (`{user_to_add}`) إدمـن فـي الـسـورس.**")
                    else:
                        await event.edit("⚠️ **هذا المستخدم مـوجـود بـالـفـعـل فـي قـائـمـة الإدمـنـيـة.**")
                else:
                    await event.edit("❌ **يـرجى الـرد على رسـالـة أو كتابة الايدي بـعـد الأمـر.**")

            # أمر تنزيل إدمن (للمالك فقط)
            elif cmd.startswith(".تنزيل") and sender_id == my_id:
                user_to_rem = None
                if event.is_reply:
                    reply_msg = await event.get_reply_message()
                    user_to_rem = reply_msg.sender_id
                else:
                    parts = cmd.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        user_to_rem = int(parts[1])
                
                if user_to_rem in admins_list:
                    admins_list.remove(user_to_rem)
                    await event.edit(f"❌ **تـم تـنـزيـل الـمـسـتـخدم (`{user_to_rem}`) مـن الإدمـنـيـة.**")
                else:
                    await event.edit("⚠️ **الـمـسـتـخدم لـيـس إدمـن فـي الـسـورس.**")

            # أمر الفحص الكامل
            elif cmd == ".فحص":
                start_t = time.time()
                tz = pytz.timezone('Asia/Baghdad')
                time_now = datetime.now(tz).strftime("%I:%M:%S %p")
                ping = round((time.time() - start_t) * 1000, 2)
                check_text = (
                    f"🛡 **تـقـريـر فـحـص سـورس ريـكـو الـمـطـور :**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👑 **صـاحـب الـحـسـاب :** [{me.first_name}](tg://user?id={me.id})\n"
                    f"👤 **الـمـرسـل :** [اضـغـط هـنـا](tg://user?id={sender_id})\n"
                    f"📡 **سـرعـة الـبـنـج :** `{ping}ms`\n"
                    f"⏰ **الـوقـت الـآن :** `{time_now}`\n"
                    f"⚙️ **الـحـالـة :** `ACTIVE ✅`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE IS THE BEST -**\n"
                    f"👨‍💻 **Dev:** {DEV_USER} | **Channel:** @{SOURCE_CH}"
                )
                try:
                    await client.send_message(event.chat_id, check_text, file=f"https://t.me/SORS_RECO/4")
                    if event.out: 
                        await event.delete()
                except Exception: 
                    if event.out: await event.edit(check_text)
                    else: await event.reply(check_text)

            elif cmd == ".الاوامر":
                help_text = (
                    f"⚜️ **قـائـمـة تـحـكـم سـورس ريـكـو الـعـالـمـي** ⚜️\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🚀 `.فحص` : لـمـعـرفـة حـالـة الـسـورس.\n"
                    f"🕒 `.وقت_تشغيل` : تـفـعـيـل الـسـاعـة بـالاسـم.\n"
                    f"✍️ `.غامق` : تـفـعـيـل الـخـط الـغـامـق.\n"
                    f"👮‍♂️ `.ادمن` : لـرفـع مـسـاعـد فـي الـسـورس.\n"
                    f"🗑 `.تنزيل` : لإزالـة إدمـن مـن الـسـورس.\n"
                    f"👤 `.ايدي` : كـشـف بـيـانـات الـتـنـصـيـب.\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE STRENGTH -**"
                )
                if event.out: await event.edit(help_text)
                else: await event.reply(help_text)

            elif cmd in [".ايدي", ".معلوماتي"]:
                full = await client(functions.users.GetFullUserRequest(me.id))
                bio = full.full_user.about or "لا يوجد نبذة"
                info_text = (
                    f"💎 **مـعـلومـات الـعـضـويـة :**\n"
                    f"👤 **الاسـم :** {me.first_name}\n"
                    f"🆔 **الايـدي :** `{me.id}`\n"
                    f"📝 **الـبـايـو :** `{bio}`\n"
                    f"📞 **الـرقـم :** `+{me.phone}`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO POWER -**"
                )
                if event.out: await event.edit(info_text)
                else: await event.reply(info_text)

            elif cmd == ".وقت_تشغيل" and sender_id == my_id:
                if not name_task or name_task.done():
                    name_task = asyncio.create_task(auto_update_name())
                    await event.edit("✅ **تـم تـفـعـيـل سـاعـة الـوقـت فـي الاسـم.**")

            elif cmd == ".وقت_إطفاء" and sender_id == my_id:
                if name_task:
                    name_task.cancel()
                    name_task = None
                    await client(functions.account.UpdateProfileRequest(first_name=original_name))
                    await event.edit("📴 **تـم إيـقـاف الـسـاعـة وتـرجـيـع الاسـم الـأصـلي.**")

            elif cmd == ".غامق" and sender_id == my_id:
                bold_enabled = True
                await event.edit("✍️ **تـم تـفـعـيـل وضـع الـخـط الـغـامـق.**")

            elif cmd == ".الغاء_غامق" and sender_id == my_id:
                bold_enabled = False
                await event.edit("🛑 **تـم إيـقـاف وضـع الـخـط الـغـامـق.**")

            # خاصية تعديل النص لغامق (فقط عند كتابة المالك)
            elif bold_enabled and event.out and event.text and not event.text.startswith("."):
                try: 
                    await event.edit(f"**{event.text}**")
                except Exception: 
                    pass

        # --- وظائف المراقبة العامة (حفظ الميديا والتوجيه) ---
        if not event.out:
            try:
                if event.is_private:
                    if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds and save_enabled:
                        path = await event.download_media()
                        cap = f"📥 **تـم اقـتـنـاص مـيـديـا ذاتـيـة الـتـدمـيـر مـن :** `{event.sender_id}`"
                        await client.send_message("me", cap, file=path)
                        if storage_pv: 
                            await client.send_message(storage_pv, cap, file=path)
                        os.remove(path)
                    
                    elif storage_pv and not getattr((await event.get_sender()), 'bot', False) and sender_id not in admins_list:
                        await client.forward_messages(storage_pv, event.message)
                
                elif (event.is_group or event.is_channel) and storage_groups:
                    if event.chat_id not in [storage_pv, storage_groups, storage_deleted]:
                        await client.forward_messages(storage_groups, event.message)
            except Exception: 
                pass

    # --- معالج الرسائل المحذوفة (كاشف المحذوفات) ---
    @client.on(events.MessageDeleted)
    async def delete_handler(event):
        for msg_id in event.deleted_ids:
            if msg_id in msg_cache:
                old_msg = msg_cache[msg_id]['message']
                sender = await old_msg.get_sender()
                name = sender.first_name if sender else "مجهول"
                
                alert_text = (
                    f"🚨 **تـنـبـيـه: حـذف رسـالـة جـديـدة !**\n"
                    f"👤 **الـمـرسـل :** {name} (`{old_msg.sender_id}`)\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
                )
                
                await client.send_message("me", alert_text)
                if old_msg.text:
                    await client.send_message("me", f"💬 **الـنـص الـمحـذوف :**\n`{old_msg.text}`")
                
                if storage_deleted:
                    await client.send_message(storage_deleted, f"🚨 **الرسالة المحذوفة للمستخدم :** {name}")
                    if old_msg.text:
                        await client.send_message(storage_deleted, old_msg.text)
                    if old_msg.media:
                        try:
                            path = await client.download_media(old_msg)
                            await client.send_message(storage_deleted, file=path)
                            os.remove(path)
                        except:
                            await client.send_message(storage_deleted, "❌ تـعذر اسـتعادة المـيديا الـمـحذوفة.")
                
                msg_cache.pop(msg_id, None)

    # --- بدء تشغيل الحساب ---
    try:
        await client.start()
        await setup_all_storages()
        asyncio.create_task(cache_cleaner())
        print(f"✅ سـورس ريـكـو يـعـمـل الآن بـنـجـاح.")
        await client.run_until_disconnected()
    except Exception as e:
        raise e
