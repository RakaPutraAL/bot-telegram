from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import BOT_TOKEN
from database import (
    init_db,
    add_user,
    add_transaction,
    get_summary,
    get_transactions,
    reset_user_data
)


# =========================================================
# FORMAT RUPIAH
# =========================================================

def rupiah(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")


# =========================================================
# MENU UTAMA
# =========================================================

def main_menu():

    keyboard = [
        ["➕ Pemasukan", "➖ Pengeluaran"],
        ["📊 Ringkasan", "📋 Riwayat"],
        ["⚙️ Pengaturan"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(
        user.id,
        user.username,
        user.full_name
    )

    await update.message.reply_text(
        "💰 *KEUANGAN LETA*\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        "Selamat datang di bot pencatat keuangan pribadi.\n\n"
        "Kamu bisa mencatat pemasukan, pengeluaran, "
        "melihat saldo, dan melihat riwayat transaksi.\n\n"
        "Silakan pilih menu di bawah 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# PEMASUKAN
# =========================================================

async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Format salah.\n\n"
            "Gunakan:\n"
            "/masuk nominal keterangan\n\n"
            "Contoh:\n"
            "/masuk 2100000 gaji"
        )

        return

    try:
        amount = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Nominal harus berupa angka.\n\n"
            "Contoh:\n"
            "/masuk 2100000 gaji"
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Nominal harus lebih dari 0."
        )

        return

    description = " ".join(context.args[1:])

    add_transaction(
        update.effective_user.id,
        "income",
        amount,
        "Pemasukan",
        description
    )

    income, expense = get_summary(
        update.effective_user.id
    )

    balance = income - expense

    await update.message.reply_text(
        "✅ *PEMASUKAN BERHASIL DICATAT*\n\n"
        f"💰 Nominal: {rupiah(amount)}\n"
        f"📝 Keterangan: {description}\n\n"
        f"💵 Saldo bulan ini: {rupiah(balance)}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# PENGELUARAN
# =========================================================

async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) < 2:

        await update.message.reply_text(
            "❌ Format salah.\n\n"
            "Gunakan:\n"
            "/keluar nominal kategori [keterangan]\n\n"
            "Contoh:\n"
            "/keluar 15000 makan nasi goreng"
        )

        return

    try:
        amount = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Nominal harus berupa angka."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Nominal harus lebih dari 0."
        )

        return

    category = context.args[1]

    description = (
        " ".join(context.args[2:])
        if len(context.args) > 2
        else category
    )

    add_transaction(
        update.effective_user.id,
        "expense",
        amount,
        category,
        description
    )

    income, expense = get_summary(
        update.effective_user.id
    )

    balance = income - expense

    await update.message.reply_text(
        "✅ *PENGELUARAN BERHASIL DICATAT*\n\n"
        f"💸 Nominal: {rupiah(amount)}\n"
        f"📁 Kategori: {category}\n"
        f"📝 Keterangan: {description}\n\n"
        f"💵 Sisa bulan ini: {rupiah(balance)}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# RINGKASAN
# =========================================================

async def ringkasan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    income, expense = get_summary(
        update.effective_user.id
    )

    balance = income - expense

    await update.message.reply_text(
        "📊 *RINGKASAN BULAN INI*\n\n"
        f"💰 Total pemasukan\n"
        f"{rupiah(income)}\n\n"
        f"💸 Total pengeluaran\n"
        f"{rupiah(expense)}\n\n"
        f"💵 Sisa uang\n"
        f"{rupiah(balance)}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# RIWAYAT
# =========================================================

async def riwayat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = get_transactions(
        update.effective_user.id
    )

    if not data:

        await update.message.reply_text(
            "📋 *RIWAYAT TRANSAKSI*\n\n"
            "Belum ada transaksi.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

        return

    text = "📋 *RIWAYAT TRANSAKSI*\n\n"

    for row in data:

        transaction_type, amount, category, description, created_at = row

        emoji = (
            "💰"
            if transaction_type == "income"
            else "💸"
        )

        text += (
            f"{emoji} {rupiah(amount)}\n"
            f"📁 {category}\n"
            f"📝 {description}\n"
            f"🕐 {created_at}\n\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# PENGATURAN
# =========================================================

async def pengaturan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Reset Semua Data",
                callback_data="reset_data"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Tutup",
                callback_data="close_settings"
            )
        ]
    ]

    await update.message.reply_text(
        "⚙️ *PENGATURAN*\n\n"
        "Pilih pengaturan yang ingin digunakan.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# KONFIRMASI RESET
# =========================================================

async def reset_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Ya, Reset",
                callback_data="confirm_reset"
            ),
            InlineKeyboardButton(
                "❌ Batal",
                callback_data="cancel_reset"
            )
        ]
    ]

    await query.edit_message_text(
        "⚠️ *PERINGATAN RESET DATA*\n\n"
        "Semua data berikut akan dihapus:\n\n"
        "💰 Pemasukan\n"
        "💸 Pengeluaran\n"
        "🎯 Budget\n"
        "💵 Target tabungan\n\n"
        "Data yang sudah dihapus tidak dapat dikembalikan.\n\n"
        "*Apakah kamu yakin ingin melanjutkan?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# RESET DATA
# =========================================================

async def confirm_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    reset_user_data(user_id)

    await query.edit_message_text(
        "✅ *DATA BERHASIL DIRESET*\n\n"
        "Semua data keuangan kamu telah dihapus.\n\n"
        "Sekarang akun kamu kembali seperti baru. 💰",
        parse_mode="Markdown"
    )


# =========================================================
# BATAL RESET
# =========================================================

async def cancel_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "❌ Reset dibatalkan.\n\n"
        "Data keuangan kamu tetap aman. 🔒"
    )


# =========================================================
# TUTUP PENGATURAN
# =========================================================

async def close_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "⚙️ Pengaturan ditutup."
    )


# =========================================================
# TOMBOL MENU
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if text == "➕ Pemasukan":

        await update.message.reply_text(
            "➕ *TAMBAH PEMASUKAN*\n\n"
            "Gunakan format:\n\n"
            "/masuk nominal keterangan\n\n"
            "Contoh:\n"
            "/masuk 2100000 gaji",
            parse_mode="Markdown"
        )

    elif text == "➖ Pengeluaran":

        await update.message.reply_text(
            "➖ *TAMBAH PENGELUARAN*\n\n"
            "Gunakan format:\n\n"
            "/keluar nominal kategori keterangan\n\n"
            "Contoh:\n"
            "/keluar 15000 makan nasi goreng",
            parse_mode="Markdown"
        )

    elif text == "📊 Ringkasan":

        await ringkasan(update, context)

    elif text == "📋 Riwayat":

        await riwayat(update, context)

    elif text == "⚙️ Pengaturan":

        await pengaturan(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    # Membuat tabel jika belum ada
    init_db()

    # Membuat aplikasi Telegram
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("masuk", masuk)
    )

    app.add_handler(
        CommandHandler("keluar", keluar)
    )

    app.add_handler(
        CommandHandler("ringkasan", ringkasan)
    )

    app.add_handler(
        CommandHandler("riwayat", riwayat)
    )

    # Tombol menu
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler
        )
    )

    # Tombol konfirmasi/reset
    app.add_handler(
        CallbackQueryHandler(
            reset_confirmation,
            pattern="^reset_data$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            confirm_reset,
            pattern="^confirm_reset$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            cancel_reset,
            pattern="^cancel_reset$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            close_settings,
            pattern="^close_settings$"
        )
    )

    print(
        "🤖 Keuangan Leta Bot sedang berjalan..."
    )

    app.run_polling()


# =========================================================
# JALANKAN PROGRAM
# =========================================================

if __name__ == "__main__":
    main()