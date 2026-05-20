import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from tts import generate_voice
from audio_mixer import mix_audio
from subscription import is_subscribed, add_user, remove_user, list_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))


# ─── COMMANDES ADMIN ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_subscribed(user_id):
        await update.message.reply_text(
            "👋 Bonjour ! Ce bot est accessible sur abonnement.\n"
            "Contactez l'administrateur pour obtenir l'accès."
        )
        return
    await update.message.reply_text(
        "🎙️ *Bot Vocal actif !*\n\n"
        "Envoyez votre message texte et il sera converti en vocal.\n\n"
        "*Sons disponibles (à insérer dans votre texte) :*\n"
        "• `/toux` — toux\n"
        "• `/baillement` — bâillement\n"
        "• `/rire` — rire\n"
        "• `/soupir` — soupir\n"
        "• `/hmm` — hésitation\n"
        "• `/pause` — silence\n\n"
        "*Exemple :*\n"
        "`coucou ! /toux c'est Julia, tu vas bien ?`",
        parse_mode="Markdown"
    )

async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /adduser <user_id>")
        return
    uid = int(context.args[0])
    add_user(uid)
    await update.message.reply_text(f"✅ Utilisateur {uid} ajouté.")

async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeuser <user_id>")
        return
    uid = int(context.args[0])
    remove_user(uid)
    await update.message.reply_text(f"🗑️ Utilisateur {uid} supprimé.")

async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = list_users()
    if not users:
        await update.message.reply_text("Aucun utilisateur abonné.")
        return
    txt = "👥 *Abonnés actifs :*\n" + "\n".join(f"• `{u}`" for u in users)
    await update.message.reply_text(txt, parse_mode="Markdown")

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Votre Telegram ID : `{update.effective_user.id}`", parse_mode="Markdown")


# ─── MESSAGE PRINCIPAL ─────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_subscribed(user_id):
        await update.message.reply_text(
            "🔒 Accès réservé aux abonnés. Contactez l'administrateur."
        )
        return

    text = update.message.text.strip()
    if not text:
        return

    # Indicateur "enregistrement en cours"
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="record_voice"
    )

    try:
        # Génération du vocal + mixage des sons
        output_path = await mix_audio(text)

        with open(output_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

        # Nettoyage fichier temporaire
        os.remove(output_path)

    except Exception as e:
        logger.error(f"Erreur génération audio : {e}")
        await update.message.reply_text(
            "❌ Erreur lors de la génération du vocal. Réessayez."
        )


# ─── LANCEMENT ─────────────────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN manquant dans les variables d'environnement")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("removeuser", cmd_removeuser))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot démarré ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
