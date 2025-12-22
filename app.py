from telethon import TelegramClient, events, functions, types
import asyncio
import os
import time
from datetime import datetime
import pytz

# --- بيانات الاعتماد ---
api_id = 28494906
api_hash = "004295a4ebda27f44ecb312215f10284"

# تثبيت اسم الجلسة من ملفك الموجود فعلياً لضمان عدم طلب كود جديد
client = TelegramClient("reco_final", api_id, api_hash)

# --- إعدادات النظام ---
VIDEO_SOURCE = "SORS_RECO" 
VIDEO_ID = 4               
self_destruct_save_enabled = True 
name_task = None
storage_group_id = None 

# خطوط الأرقام المزخرفة لساعة الاسم
fonts = {"0":"𝟘","1":"𝟙","2":"𝟚","3":"𝟛","4":"𝟜","5":"𝟝","6":"𝟞","7":"𝟟","8":"𝟠","9":"𝟡",":":":","A":"𝔸","P":"ℙ","M":"𝕄"}

def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

# --- وظيفة إعداد مجموعة التخزين (المخزن) ---
async def setup_storage_group():
    global storage_group_id
    try:
        # البحث عن مجموعة باسم "RECO STORAGE"
        async for dialog in client.iter_dialogs():
            if dialog.is_group and dialog.name == "RECO STORAGE":
                storage_group_id = dialog.id
                print(f"✅ تم العثور على المخزن مسبقاً: {storage_group_id}")
                return
        
        # إنشاء واحدة جديدة إذا لم تكن موجودة
        print("⏳ جاري إنشاء مجموعة التخزين التلقائية...")
        result = await client(functions.messages.CreateChatRequest(
            title="RECO STORAGE",
            users=["me"]
        ))
        storage_group_id = result.chats[0].id
        
        tz = pytz.timezone('Asia/Baghdad')
        date_now = datetime.now(tz).strftime("%Y-%m-%d")
        about_text = f"📦 سورس ريكو - مخزن الرسائل\n📅 تأسس في: {date_now}\n🆔 ايدي المخزن: {storage_group_id}\n🦅"
        
        try:
            await client(functions.messages.EditChatAboutRequest(
                peer=storage_group_id,
                about=about_text
            ))
        except: pass
        print(f"✅ تم إنشاء المخزن وإعداده بنجاح.")
    except Exception as e:
        print(f"⚠️ تنبيه المخزن: {e}")

# --- ميزة ساعة الاسم (بغداد) ---
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

# --- المعالج الرئيسي (الخزن، الاقتناص، الأوامر) ---
@client.on(events.NewMessage)
async def main_handler(event):
    global self_destruct_save_enabled, name_task, storage_group_id
    
    # 1. أوامر التحكم (تعمل عند إرسالها منك فقط)
    if event.out:
        if event.raw_text == ".فحص":
            start_t = time.time()
            me = await client.get_me()
            tz = pytz.timezone('Asia/Baghdad')
            time_now = datetime.now(tz).strftime("%I:%M:%S %p")
            ping = round((time.time() - start_t) * 1000, 2)
            
            check_text = (
                f"🛡 **تـقـريـر سـورس ريـكـو الـمـطـور :**\n"
                f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                f"👤 **صاحب السورس :** {me.first_name}\n"
                f"📡 **سـرعـة الـبـنـج :** `{ping}ms`\n"
                f"⏰ **الـوقـت (بغداد) :** `{time_now}`\n"
                f"📦 **حالة المخزن :** {'متصل ✅' if storage_group_id else 'غير مفعل ❌'}\n"
                f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                f"🦅 **- RECO SOURCE ACTIVE -**"
            )
            try:
                await client.send_message(event.chat_id, check_text, file=f"https://t.me/{VIDEO_SOURCE}/{VIDEO_ID}")
                await event.delete()
            except: await event.edit(check_text)
            return

        elif event.raw_text == ".الاوامر":
            help_text = (
                f"👑 **أوامـر سـورس ريـكـو الـمـلكيـة**\n"
                f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                f"🔹 `.فحص` : فحص سرعة السورس.\n"
                f"🔹 `.ذاتيه` : تفعيل اقتناص الميديا.\n"
                f"🔹 `.تعطيل الذاتيه` : إيقاف الاقتناص.\n"
                f"🔹 `.وقت_تشغيل` : تفعيل الساعة بالاسم.\n"
                f"🔹 `.وقت_إطفاء` : إيقاف ساعة الاسم.\n"
                f"🔹 `.ايدي` : عرض ايديك.\n"
                f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
            )
            await event.edit(help_text)
            return

        elif event.raw_text == ".ذاتيه":
            self_destruct_save_enabled = True
            await event.edit("✅ **تم تفعيل حفظ الوسائط ذاتية التدمير**")
            return

        elif event.raw_text == ".تعطيل الذاتيه":
            self_destruct_save_enabled = False
            await event.edit("🚫 **تم إيقاف حفظ الوسائط ذاتية التدمير**")
            return

        elif event.raw_text == ".وقت_تشغيل":
            if not name_task or name_task.done():
                name_task = asyncio.create_task(auto_update_name())
                await event.edit("✨ **تم تفعيل ساعة الاسم.**")
            else: await event.edit("⚠️ **تعمل بالفعل.**")
            return

        elif event.raw_text == ".وقت_إطفاء":
            if name_task:
                name_task.cancel()
                name_task = None
                await client(functions.account.UpdateProfileRequest(first_name="RECO"))
                await event.edit("📴 **تم إيقاف ساعة الاسم.**")
            return

        elif event.raw_text == ".ايدي":
            await event.edit(f"🎫 **ايدي حسابك:** `{event.sender_id}`")
            return

    # 2. منطق حفظ الذاتية (حسب الكود الذي زودتني به)
    if not event.out and event.is_private and self_destruct_save_enabled:
        if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds:
            try:
                sender = await event.get_sender()
                sender_name = sender.first_name or "مجهول"
                file_path = await event.download_media()
                
                if file_path:
                    caption = (
                        f"📥 **تم حفظ وسائط ذاتية التدمير**\n"
                        f"👤 من: {sender_name}\n"
                        f"🆔 الآيدي: `{event.sender_id}`"
                    )
                    # الحفظ في الرسائل المحفوظة والمخزن
                    await client.send_message("me", caption, file=file_path)
                    if storage_group_id:
                        await client.send_message(storage_group_id, caption, file=file_path)
                    
                    os.remove(file_path)
                    print(f"✅ تم اقتناص ميديا من {event.sender_id}")
            except Exception as e:
                print(f"❌ خطأ في الحفظ: {e}")

    # 3. ميزة المخزن (خزن الرسائل العادية)
    if not event.out and event.is_private and storage_group_id:
        # نتحقق أنها ليست رسالة تدمير ذاتي (لأننا عالجناها في الخطوة 2)
        if not (event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds):
            sender = await event.get_sender()
            if sender and not getattr(sender, 'bot', False):
                try:
                    await client.forward_messages(storage_group_id, event.message)
                except: pass

# --- تشغيل النظام ---
async def start_reco_system():
    print("🚀 جاري الاتصال باستخدام الجلسة المستقرة...")
    await client.start()
    
    # إعداد المخزن عند بدء التشغيل
    await setup_storage_group()
    
    print("✅ سورس ريكو المطور شغال الآن بكامل مميزاته!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_reco_system())
