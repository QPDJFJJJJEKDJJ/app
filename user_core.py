from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import CreateChatRequest
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio, os, time, pytz
from datetime import datetime

# الأرقام المزخرفة للساعة
fonts = {
    "0":"𝟘","1":"𝟙","2":"𝟚","3":"𝟛","4":"𝟜","5":"𝟝","6":"𝟞","7":"𝟟","8":"𝟠","9":"𝟡",
    ":":":","A":"𝔸","P":"ℙ","M":"𝕄"
}

def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

async def start_user_source(session_str, api_id, api_hash, install_info=None):
    # إنشاء العميل
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    
    # متغيرات الحالة
    save_enabled = True
    storage_pv = None    
    storage_groups = None 
    storage_deleted = None 
    name_task = None 
    original_name = "" 
    DEV_USER = "@I_QQ_Q"
    SOURCE_CH = "SORS_RECO"
    start_time = datetime.now()

    # مخزن مؤقت (Cache) لحفظ محتوى الرسائل بالكامل لمواجهة الحذف
    msg_cache = {}

    # --- ميزة تحديث الوقت بجانب الاسم ---
    async def auto_update_name():
        nonlocal original_name
        try:
            me = await client.get_me()
            original_name = me.first_name.split('|')[0].strip()
        except: 
            original_name = "User"
        while True:
            try:
                tz = pytz.timezone('Asia/Baghdad')
                t_str = datetime.now(tz).strftime("%I:%M %p")
                styled_t = get_styled_time(t_str)
                await client(functions.account.UpdateProfileRequest(first_name=f"{original_name} | {styled_t}"))
                await asyncio.sleep(60)
            except asyncio.CancelledError: 
                break
            except: 
                await asyncio.sleep(10)

    # --- دالة إنشاء الكروبات ---
    async def create_and_get_id(title):
        try:
            result = await client(CreateChatRequest(title=title, users=["me"]))
            if hasattr(result, 'chats') and result.chats:
                return result.chats[0].id
            else:
                async for dialog in client.iter_dialogs(limit=20):
                    if dialog.name == title: 
                        return dialog.id
        except Exception as e:
            print(f"Error creating {title}: {e}")
            return None

    # --- إعداد المجموعات والانضمام للقناة ---
    async def setup_all_storages():
        nonlocal storage_pv, storage_groups, storage_deleted
        # 1. الانضمام لقناة السورس
        try:
            await client(JoinChannelRequest(SOURCE_CH))
        except:
            pass

        # 2. البحث عن المجموعات الموجودة
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                if dialog.name == "RECO PV STORAGE": storage_pv = dialog.id
                elif dialog.name == "RECO GROUPS STORAGE": storage_groups = dialog.id
                elif dialog.name == "RECO DELETED STORAGE": storage_deleted = dialog.id
        
        # 3. إنشاء المجموعات إذا لم تكن موجودة
        if not storage_pv: 
            storage_pv = await create_and_get_id("RECO PV STORAGE")
        if not storage_groups: 
            storage_groups = await create_and_get_id("RECO GROUPS STORAGE")
        if not storage_deleted: 
            storage_deleted = await create_and_get_id("RECO DELETED STORAGE")

    # --- المعالج الرئيسي للرسائل ---
    @client.on(events.NewMessage)
    async def main_handler(event):
        nonlocal save_enabled, name_task
        
        # تخزين كل رسالة خاصة في الكاش فور وصولها (حتى لو حذفت لاحقاً)
        if event.is_private and not event.out:
            msg_cache[event.id] = event.message
            if len(msg_cache) > 1000:
                # إزالة أقدم رسالة للحفاظ على الذاكرة
                msg_cache.pop(next(iter(msg_cache)))

        # الأوامر الصادرة من المستخدم
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
                    f"📡 **سـرعـة الاسـتـجـابـة :** `{ping}ms`\n"
                    f"⏰ **الـوقـت الـحـالـي :** `{time_now}`\n"
                    f"⚙️ **الـحـالـة :** `ACTIVE ✅`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE IS THE BEST -**\n"
                    f"👨‍💻 **Dev:** {DEV_USER} | **Channel:** @{SOURCE_CH}"
                )
                try:
                    await client.send_message(event.chat_id, check_text, file=f"https://t.me/SORS_RECO/4")
                    await event.delete()
                except: 
                    await event.edit(check_text)

            elif event.raw_text == ".الاوامر":
                help_text = (
                    f"⚜️ **قـائـمـة تـحـكـم سـورس ريـكـو الـعـالـمـي** ⚜️\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🚀 `.فحص` : لـمـعـرفـة حـالـة الـسـورس.\n"
                    f"📸 `.ذاتيه` : تـفـعـيـل حـفـظ الـمـيـديـا الـمـخـفـيـة.\n"
                    f"🕒 `.وقت_تشغيل` : تـفـعـيـل الـسـاعـة بـجـانـب اسـمـك.\n"
                    f"👤 `.ايدي` | `.معلوماتي` : كـشـف بـيـانـات الـتـنـصـيـب.\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE STRENGTH -**"
                )
                await event.edit(help_text)

            elif event.raw_text in [".ايدي", ".معلوماتي"]:
                me = await client.get_me()
                full = await client(functions.users.GetFullUserRequest(me.id))
                bio = full.full_user.about or "لا يوجد نبذة"
                info_text = (
                    f"💎 **مـعـلومـات الـعـضـويـة :**\n"
                    f"👤 **الاسـم :** {me.first_name}\n"
                    f"🆔 **الايـدي :** `{me.id}`\n"
                    f"📝 **الـبـايـو :** `{bio}`\n"
                    f"🦅 **Dev:** {DEV_USER}"
                )
                await event.edit(info_text)

            elif event.raw_text == ".وقت_تشغيل":
                if not name_task or name_task.done():
                    name_task = asyncio.create_task(auto_update_name())
                    await event.edit(f"✅ **تـم تـفـعـيـل سـاعـة الاسـم.**")

            elif event.raw_text == ".وقت_إطفاء":
                if name_task:
                    name_task.cancel(); name_task = None
                    await client(functions.account.UpdateProfileRequest(first_name=original_name))
                    await event.edit("📴 **تـم إيـقـاف سـاعـة الاسـم.**")

        # --- نظام التخزين والتحويل ---
        if not event.out:
            try:
                # 1. تخزين رسائل الخاص
                if event.is_private:
                    if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds and save_enabled:
                        path = await event.download_media()
                        cap = "📥 **تـم اقـتـنـاص مـيـديـا ذاتـيـة الـتـدمـيـر !**"
                        await client.send_message("me", cap, file=path)
                        if storage_pv: await client.send_message(storage_pv, cap, file=path)
                        os.remove(path)
                    elif storage_pv and not getattr((await event.get_sender()), 'bot', False):
                        await client.forward_messages(storage_pv, event.message)
                
                # 2. تخزين رسائل المجموعات والقنوات
                elif (event.is_group or event.is_channel) and storage_groups:
                    if event.chat_id not in [storage_pv, storage_groups, storage_deleted]:
                        await client.forward_messages(storage_groups, event.message)
            except: 
                pass

    # --- معالج المحذوفات (حل مشكلة MessageIdInvalidError) ---
    @client.on(events.MessageDeleted)
    async def delete_handler(event):
        for msg_id in event.deleted_ids:
            if msg_id in msg_cache:
                old_msg = msg_cache[msg_id]
                sender = await old_msg.get_sender()
                name = sender.first_name if sender else "مجهول"
                
                alert_text = (
                    f"⚠️ **تـم حـذف رسـالـة مـن الـخـاص !**\n"
                    f"👤 **الـمـرسـل :** {name} (`{old_msg.sender_id}`)\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
                )
                
                # 1. إرسال تنبيه في المحفوظات
                await client.send_message("me", alert_text)
                if old_msg.text:
                    await client.send_message("me", f"💬 **نص الرسالة المحذوفة:**\n`{old_msg.text}`")
                
                # 2. إرسال المحتوى لكروب المحذوفات كرسالة جديدة (لتجنب خطأ التحويل)
                if storage_deleted:
                    await client.send_message(storage_deleted, f"🚨 **الرسالة المحذوفة للمستخدم :** {name}")
                    if old_msg.text:
                        await client.send_message(storage_deleted, old_msg.text)
                    if old_msg.media:
                        try:
                            # تحميل الميديا من الذاكرة وإعادة إرسالها
                            path = await client.download_media(old_msg)
                            await client.send_message(storage_deleted, file=path)
                            os.remove(path)
                        except:
                            await client.send_message(storage_deleted, "❌ تعذر استعادة الميديا المحذوفة.")
                
                # حذف من الذاكرة
                msg_cache.pop(msg_id)

    # تشغيل العميل
    await client.start()
    await setup_all_storages()
    print(f"✅ الحساب جاهز للعمل مع مراقبة المحذوفات.")
    await client.run_until_disconnected()
