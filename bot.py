import logging
import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters, ContextTypes,
)
from config import BOT_TOKEN, DIA_PHUONG, HEADERS
from vbpl_api import tra_cuu_van_ban, xac_dinh_trang_thai

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

NHAP_SO_KY_HIEU, CHON_DIA_PHUONG = range(2)

def build_dia_phuong_keyboard():
    row = [InlineKeyboardButton(name, callback_data=f"dp_{code}")
           for code, name in DIA_PHUONG.items()]
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("❌ Huỷ", callback_data="huy")]])

def build_result_keyboard(vb_id, files, vb_url=""):
    buttons = []
    for i, f in enumerate(files[:4]):
        label = f"📥 [{f.get('loai','FILE')}] {f.get('ten','Tải file')[:35]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"dl_{vb_id}_{i}")])
    nav = [InlineKeyboardButton("🔍 Tra cứu văn bản khác", callback_data="tracuu_lai")]
    if vb_url:
        nav.append(InlineKeyboardButton("🌐 Xem trên vbpl.vn", url=vb_url))
    buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚖️ *BOT TRA CỨU VĂN BẢN PHÁP LUẬT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Hỗ trợ tra cứu văn bản quy phạm pháp luật từ [vbpl.vn](https://vbpl.vn):\n\n"
        "🛢️ *Bà Rịa - Vũng Tàu*\n"
        "🏭 *Bình Dương*\n"
        "🏙️ *TP. Hồ Chí Minh*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 Gõ /tracuu để bắt đầu\n"
        "👉 Gõ /help để xem hướng dẫn",
        parse_mode="Markdown", disable_web_page_preview=True,
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *HƯỚNG DẪN SỬ DỤNG*\n\n"
        "*Bước 1:* Gõ /tracuu\n"
        "*Bước 2:* Nhập số ký hiệu văn bản\n"
        "   VD: `01/2023/NĐ-CP`\n"
        "   VD: `100/2024/QĐ-UBND`\n\n"
        "*Bước 3:* Chọn địa phương\n"
        "*Bước 4:* Xem kết quả → tải file\n\n"
        "✅ Còn hiệu lực  ❌ Hết hiệu lực\n"
        "⚠️ Một phần      🕐 Chưa hiệu lực",
        parse_mode="Markdown",
    )

async def cmd_tracuu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Nhập *số ký hiệu* văn bản cần tra cứu:\n\n"
        "📌 _VD: `01/2023/NĐ-CP`_\n\n❌ Gõ /huy để huỷ",
        parse_mode="Markdown",
    )
    return NHAP_SO_KY_HIEU

async def nhan_so_ky_hieu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    so_ky_hieu = update.message.text.strip()
    context.user_data["so_ky_hieu"] = so_ky_hieu
    await update.message.reply_text(
        f"📄 Số ký hiệu: `{so_ky_hieu}`\n\n🏛️ Chọn *địa phương ban hành:*",
        reply_markup=build_dia_phuong_keyboard(),
        parse_mode="Markdown",
    )
    return CHON_DIA_PHUONG

async def chon_dia_phuong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dp_code    = query.data.replace("dp_", "")
    dp_name    = DIA_PHUONG.get(dp_code, dp_code)
    so_ky_hieu = context.user_data.get("so_ky_hieu", "")

    await query.edit_message_text(
        f"⏳ *Đang tra cứu...*\n\n"
        f"📄 Số ký hiệu: `{so_ky_hieu}`\n"
        f"🏛️ Địa phương: {dp_name}\n\n_Vui lòng chờ..._",
        parse_mode="Markdown",
    )

    results = tra_cuu_van_ban(so_ky_hieu, dp_code)

    if not results:
        await query.edit_message_text(
            f"❌ *Không tìm thấy văn bản*\n\n"
            f"📄 `{so_ky_hieu}` — {dp_name}\n\n"
            "💡 Kiểm tra lại số ký hiệu hoặc thử địa phương khác.\n"
            "👉 Gõ /tracuu để tìm lại",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await query.delete_message()

    for r in results:
        vb_id    = r.get("id", "0")
        icon, tt = xac_dinh_trang_thai(r.get("trang_thai", ""))
        files    = r.get("files", [])
        vb_url   = r.get("url", "")

        msg = (
            f"📋 *KẾT QUẢ TRA CỨU*\n{'━'*30}\n\n"
            f"📌 *{r.get('ten', 'Không có tên')}*\n\n"
            f"🔢 *Số ký hiệu:* `{r.get('so_ky_hieu', so_ky_hieu)}`\n"
            f"📋 *Loại VB:* {r.get('loai_van_ban', 'N/A')}\n"
            f"🏛️ *Cơ quan:* {r.get('co_quan_ban_hanh', dp_name)}\n"
            f"📅 *Ngày ban hành:* {r.get('ngay_ban_hanh', 'N/A')}\n"
            f"📆 *Ngày hiệu lực:* {r.get('ngay_hieu_luc', 'N/A')}\n\n"
            f"{'━'*30}\n{icon} *TRẠNG THÁI: {tt}*\n{'━'*30}\n"
        )

        vb_td = r.get("van_ban_tac_dong", [])
        if vb_td and ("HẾT" in tt or "MỘT PHẦN" in tt):
            msg += "\n🔄 *Bị tác động bởi:*\n"
            for vb in vb_td[:4]:
                loai = vb.get("loai_tac_dong", "Tác động")
                skh  = vb.get("so_ky_hieu", "")
                ten  = vb.get("ten", "")
                url  = vb.get("url", "")
                msg += f"  • [{loai}] `{skh}` — [{ten}]({url})\n" if url else f"  • [{loai}] `{skh}` — {ten}\n"

        trich_yeu = r.get("trich_yeu", "")
        if trich_yeu:
            short = trich_yeu[:200] + "…" if len(trich_yeu) > 200 else trich_yeu
            msg  += f"\n📝 *Trích yếu:*\n_{short}_\n"

        context.user_data[f"files_{vb_id}"] = files

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            parse_mode="Markdown",
            reply_markup=build_result_keyboard(vb_id, files, vb_url),
            disable_web_page_preview=False,
        )
    return ConversationHandler.END

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Đang chuẩn bị tải file...")
    parts = query.data.split("_")
    if len(parts) < 3:
        await query.answer("❌ Lỗi xác định file!", show_alert=True)
        return
    vb_id    = parts[1]
    file_idx = int(parts[2])
    files    = context.user_data.get(f"files_{vb_id}", [])
    if not files or file_idx >= len(files):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="❌ Không tìm thấy file.")
        return
    f        = files[file_idx]
    file_url = f["url"]
    ext      = f.get("loai", "pdf").lower()
    filename = f"{f.get('ten', 'vanban')[:50]}.{ext}"
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"⏳ Đang tải: *{f.get('ten','file')}*...",
        parse_mode="Markdown",
    )
    try:
        resp = requests.get(file_url, headers=HEADERS, timeout=60)
        if resp.status_code == 200:
            size_mb = len(resp.content) / 1024 / 1024
            if size_mb > 50:
                await msg.edit_text(f"⚠️ File quá lớn ({size_mb:.1f}MB).\n📎 Tải trực tiếp:\n{file_url}")
                return
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=BytesIO(resp.content),
                filename=filename,
                caption=f"📄 *{f.get('ten','Văn bản')}*\n📦 {len(resp.content)//1024} KB\n🔗 vbpl.vn",
                parse_mode="Markdown",
            )
            await msg.delete()
        else:
            await msg.edit_text(f"❌ HTTP {resp.status_code}.\n📎 {file_url}")
    except Exception as e:
        logger.error(f"[DL] {e}")
        await msg.edit_text(f"❌ Lỗi tải file.\n📎 {file_url}")

async def huy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "✅ Đã huỷ. Gõ /tracuu để tra cứu mới."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(txt)
    else:
        await update.message.reply_text(txt)
    context.user_data.clear()
    return ConversationHandler.END

async def tracuu_lai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔍 Nhập *số ký hiệu* văn bản:\n\n_VD: 01/2023/NĐ-CP_",
        parse_mode="Markdown",
    )
    return NHAP_SO_KY_HIEU

async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN chưa được đặt trong biến môi trường!")
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("tracuu", cmd_tracuu),
            CallbackQueryHandler(tracuu_lai, pattern="^tracuu_lai$"),
        ],
        states={
            NHAP_SO_KY_HIEU: [MessageHandler(filters.TEXT & ~filters.COMMAND, nhan_so_ky_hieu)],
            CHON_DIA_PHUONG: [
                CallbackQueryHandler(chon_dia_phuong, pattern=r"^dp_"),
                CallbackQueryHandler(huy, pattern="^huy$"),
            ],
        },
        fallbacks=[
            CommandHandler("huy", huy),
            CallbackQueryHandler(huy, pattern="^huy$"),
        ],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(download_file, pattern=r"^dl_"))
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))
    logger.info("✅ Bot đang chạy...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
