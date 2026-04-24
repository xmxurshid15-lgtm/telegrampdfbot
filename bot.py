import os
import img2pdf
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== KONFIGURATSIYA ====================
TOKEN = "8645720663:AAEz5BTaAvxsRt8ETyZz3ZD2FgQjTLfO0VE"

# ASOSCHI NIKI
CREATOR = "@husanov_15"

# ==================== SIFAT SOZLAMALARI ====================
QUALITY_SETTINGS = {
    'low': {'name': 'Past sifat', 'size': (800, 800), 'quality': 50},
    'medium': {'name': 'Orta sifat', 'size': (1280, 1280), 'quality': 75},
    'high': {'name': 'Yuqori sifat', 'size': (1920, 1920), 'quality': 95}
}

# ==================== MA'LUMOTLAR ==================
user_settings = {}
user_images = {}

# ==================== TUGMALAR ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("PDF yasash", callback_data="make_pdf")],
        [InlineKeyboardButton("Rasmlarni tozalash", callback_data="clear")],
        [InlineKeyboardButton("Sifat sozlamalari", callback_data="quality_settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("Past sifat", callback_data="set_quality_low")],
        [InlineKeyboardButton("Orta sifat", callback_data="set_quality_medium")],
        [InlineKeyboardButton("Yuqori sifat", callback_data="set_quality_high")],
        [InlineKeyboardButton("Orqaga", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== RASMNI SIQISH ====================
def compress_image(input_path, output_path, quality_level):
    try:
        setting = QUALITY_SETTINGS[quality_level]
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                img = rgb_img
            max_size = setting['size']
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=setting['quality'], optimize=True)
            return True
    except Exception as e:
        print(f"Xatolik: {e}")
        return False

# ==================== YORDAMCHI FUNKSIYA ====================
async def send_or_edit_message(update, context, user_id, text):
    """Xabar yuborish yoki tahrirlash"""
    try:
        if 'last_message_id' in context.user_data:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=context.user_data['last_message_id'],
                text=text,
                reply_markup=get_main_keyboard()
            )
        else:
            msg = await update.message.reply_text(text, reply_markup=get_main_keyboard())
            context.user_data['last_message_id'] = msg.message_id
    except:
        msg = await update.message.reply_text(text, reply_markup=get_main_keyboard())
        context.user_data['last_message_id'] = msg.message_id

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id not in user_settings:
        user_settings[user_id] = {'quality': 'medium'}
    if user_id not in user_images:
        user_images[user_id] = []
    
    current_quality = user_settings[user_id]['quality']
    quality_name = QUALITY_SETTINGS[current_quality]['name']
    
    # Xabar ID sini tozalash (yangi boshlash uchun)
    context.user_data['last_message_id'] = None
    
    await update.message.reply_text(
        f"Salom {user_name}!\n\n"
        f"Menga rasm yuboring, PDF ga aylantiraman.\n\n"
        f"Hozirgi sifat: {quality_name}\n\n"
        f"Qanday ishlatiladi:\n"
        f"1) Rasmlar yuboring\n"
        f"2) 'PDF yasash' tugmasini bosing\n"
        f"3) PDF tayyor!\n"
        f"4) Yana rasmlar yuboring - YANGI PDF!\n\n"
        f"Cheksiz PDF yaratish imkoniyati!\n\n"
        f"{CREATOR}",
        reply_markup=get_main_keyboard()
    )

# ==================== HEALTH CHECK (UPTIMEROBOT UCHUN) ====================
# 🆕 YANGI QO'SHILDI - Bot uxlab qolmasligi uchun
async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """UptimeRobot botni tekshirishi uchun - bot uxlab qolmasligi kerak"""
    await update.message.reply_text("✅ Bot ishlayapti va sog'lom!")

# ==================== RASM QABUL QILISH ====================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_settings:
        user_settings[user_id] = {'quality': 'medium'}
    if user_id not in user_images:
        user_images[user_id] = []
    
    quality_level = user_settings[user_id]['quality']
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    temp_path = f"temp_{user_id}_{len(user_images[user_id])}.jpg"
    await file.download_to_drive(temp_path)
    
    final_path = f"img_{user_id}_{len(user_images[user_id])}.jpg"
    compress_image(temp_path, final_path, quality_level)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    user_images[user_id].append(final_path)
    photo_count = len(user_images[user_id])
    quality_name = QUALITY_SETTINGS[quality_level]['name']
    
    text = f"{photo_count} ta rasm saqlandi!\n\nSifat: {quality_name}\n\nYana rasm yuboring yoki pastdagi 'PDF yasash' tugmasini bosing.\n\n{CREATOR}"
    
    await send_or_edit_message(update, context, user_id, text)

# ==================== MATN XABAR ====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = f"Iltimos, rasm yuboring!\n\nRasm yuborish uchun papka belgisini bosing.\n\n{CREATOR}"
    await send_or_edit_message(update, context, user_id, text)

# ==================== TUGMALAR BOSILGANDA ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    
    if action == "make_pdf":
        await make_pdf(query, context, user_id)
    elif action == "clear":
        await clear_images(query, context, user_id)
    elif action == "quality_settings":
        await show_quality_settings(query, context, user_id)
    elif action == "back_to_main":
        await back_to_main(query, context, user_id)
    elif action.startswith("set_quality_"):
        quality_level = action.replace("set_quality_", "")
        await set_quality(query, context, user_id, quality_level)

# ==================== PDF YASASH ====================
async def make_pdf(query, context, user_id):
    if user_id not in user_images or not user_images[user_id]:
        await query.edit_message_text(
            f"Hech qanday rasm topilmadi!\n\nAvval menga rasm yuboring.\n\n{CREATOR}",
            reply_markup=get_main_keyboard()
        )
        context.user_data['last_message_id'] = None
        return
    
    quality_level = user_settings[user_id]['quality']
    quality_name = QUALITY_SETTINGS[quality_level]['name']
    pdf_path = f"output_{user_id}.pdf"
    
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(user_images[user_id]))
        
        file_size = os.path.getsize(pdf_path) / (1024 * 1024)
        photo_count = len(user_images[user_id])
        
        caption = f"Tayyor!\n\n{photo_count} ta rasm\nSifat: {quality_name}\nHajm: {file_size:.2f} MB\n\n{CREATOR}"
        
        with open(pdf_path, "rb") as pdf_file:
            await query.message.reply_document(
                pdf_file,
                filename="rasmlar.pdf",
                caption=caption
            )
        
        # RASMLARNI TOZALASH
        for img in user_images[user_id]:
            if os.path.exists(img):
                os.remove(img)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        user_images[user_id] = []
        
        # XABAR ID SINI TOZALASH (YANGI PDF UCHUN)
        context.user_data['last_message_id'] = None
        
        await query.edit_message_text(
            f"{photo_count} ta rasm PDF ga ogirildi va tozalandi!\n\n"
            f"Endi YANGI rasmlar yuborib, YANA PDF yaratishingiz mumkin!\n\n"
            f"Cheksiz PDF yaratish imkoniyati!\n\n"
            f"{CREATOR}",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"Xatolik: {str(e)}\n\nQaytadan urinib ko'ring.\n\n{CREATOR}",
            reply_markup=get_main_keyboard()
        )

# ==================== TOZALASH ====================
async def clear_images(query, context, user_id):
    if user_id in user_images and user_images[user_id]:
        count = len(user_images[user_id])
        for img in user_images[user_id]:
            if os.path.exists(img):
                os.remove(img)
        user_images[user_id] = []
        await query.edit_message_text(
            f"{count} ta rasm tozalandi!\n\nEndi yangi rasmlar yuborishingiz mumkun.\n\n{CREATOR}",
            reply_markup=get_main_keyboard()
        )
    else:
        await query.edit_message_text(
            f"Tozalash uchun hech qanday rasm yoq\n\nAvval menga rasm yuboring!\n\n{CREATOR}",
            reply_markup=get_main_keyboard()
        )

# ==================== SIFAT SOZLAMALARI ====================
async def show_quality_settings(query, context, user_id):
    current_quality = user_settings[user_id]['quality']
    current_name = QUALITY_SETTINGS[current_quality]['name']
    
    await query.edit_message_text(
        f"Sifat sozlamalari\n\n"
        f"Hozirgi: {current_name}\n\n"
        f"Past - kichik hajm\n"
        f"Orta - optimal\n"
        f"Yuqori - eng yaxshi\n\n"
        f"{CREATOR}",
        reply_markup=get_quality_keyboard()
    )

async def set_quality(query, context, user_id, quality_level):
    user_settings[user_id]['quality'] = quality_level
    quality_name = QUALITY_SETTINGS[quality_level]['name']
    
    await query.edit_message_text(
        f"Sifat ozgartirildi!\n\n"
        f"Yangi sifat: {quality_name}\n\n"
        f"Endi yuboradigan rasmlaringiz shu sifatda saqlanadi!\n\n"
        f"{CREATOR}",
        reply_markup=get_main_keyboard()
    )

async def back_to_main(query, context, user_id):
    quality_level = user_settings[user_id]['quality']
    quality_name = QUALITY_SETTINGS[quality_level]['name']
    
    await query.edit_message_text(
        f"Asosiy menyu\n\n"
        f"Hozirgi sifat: {quality_name}\n\n"
        f"Rasm yuboring!\n\n"
        f"Cheksiz PDF yaratish!\n\n"
        f"{CREATOR}",
        reply_markup=get_main_keyboard()
    )

# ==================== BOTNI ISHGA TUSHIRISH ====================
def main():
    print("Bot ishga tushmoqda...")
    print(f"Asoschi: {CREATOR}")
    print("Cheksiz PDF yaratish rejimi: YOQILDI")
    
    app = Application.builder().token(TOKEN).build()
    
    # 🆕 YANGI QO'SHILDI - health handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health))  # <--- YANGI
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot tayyor!")
    print("Har bir PDF dan keyin avtomatik tozalash YOQILDI")
    print("Cheksiz marta PDF yaratish mumkin!")
    print("")
    print("Botni sinab ko'ring: @Pdf_uzbbot")
    
    # 🆕 O'ZGARTIRILGAN QISM - Render'da webhook, kompyuterda polling
    port = int(os.environ.get("PORT", 8080))
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    
    if render_url:
        # Render cloud da ishlayapti - webhook (uxlamasligi uchun)
        print(f"Render cloud: Webhook rejimida ishga tushmoqda")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{render_url}/{TOKEN}"
        )
    else:
        # Kompyuterda yoki lokal serverda - polling (o'zgarmagan)
        print("Lokal: Polling rejimida ishga tushmoqda")
        app.run_polling()

if __name__ == "__main__":
    main()
