# FA2I Communication Agent — Telegram Bot
# Déployé sur cette machine Windows

import os
import subprocess
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# ============================================================
# CONFIGURATION
# ============================================================

# Lire le token depuis un fichier .env ou variable d'environnement
TOKEN = os.environ.get("FA2I_TELEGRAM_TOKEN") or open("token.txt").read().strip() if os.path.exists("token.txt") else ""

if not TOKEN:
    print("ERREUR : Token Telegram non trouvé.")
    print("Placez-le dans token.txt ou définissez FA2I_TELEGRAM_TOKEN.")
    exit(1)

# Dossier de travail pour les fichiers reçus
WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_files")
os.makedirs(WORK_DIR, exist_ok=True)

# ============================================================
# FONCTIONS FA2I — Logique de l'agent
# ============================================================

# Règle fondamentale — Ne jamais inventer, demander toujours
# (faites référence à la section 7 du SKILL.md pour les règles complètes)

FA2I_RULES = """
Règles FA2I :
- Ne jamais inventer d'informations sur la FA2I
- Demander les informations manquantes
- Pour les infos importantes non validées : utiliser des placeholders [NOM — À DEMANDER]
- Valider les chiffres, noms, citations avant publication
- Mode validation par défaut
"""

async def send_fa2i_response(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Envoie une réponse formatée à l'utilisateur Telegram."""
    await update.message.reply_text(message, parse_mode="Markdown")

# --- Commandes ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🇮🇩 *FA2I Communication Agent*\n\n"
        "Je suis votre assistant de production vidéo et communication.\n\n"
        "_Envoyez-moi :_\n"
        "• Des photos d'un événement\n"
        "• Des vidéos\n"
        "• Des informations textuelles sur l'événement\n"
        "• Des demandes de captions, hashtags, scripts\n\n"
        "Je produis : concepts, storyboards, captions, hashtags, plans de montage.\n\n"
        "Pour les informations importantes non vérifiées, j'utilise des placeholders.\n"
        "Je ne modifie aucun fichier sans votre validation.\n\n"
        "／contactez-moi pour toute question."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "*Commandes disponibles :*\n\n"
        "/start — Démarrer, voir les instructions\n"
        "/mode — Voir le mode actuel\n"
        "/status — Voir l'état des fichiers reçus\n"
        "/clear — Effacer les fichiers reçus ( demande confirmation)\n"
        "/config — Afficher la configuration utilisée"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "*Mode actuel :* Mode Validation (défaut)\n\n"
        "Le mode validation est actif. Toute publication demande votre confirmation.\n\n"
        "Pour activer le mode automatique : /auto_on [plateformes]\n"
        "Pour le désactiver : /auto_off"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platforms = " ".join(context.args) if context.args else "non spécifié"
    msg = (
        f"*Mode automatique activé* pour : {platforms}\n\n"
        "⚠️ Attention : le mode automatique nécessite des APIs configurées.\n"
        "Sans API, aucune publication n'est effectuée automatiquement.\n"
        "Les contenus restent programmés dans le calendrier (fichier JSON)."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "*Mode automatique désactivé.* Le mode validation est de nouveau actif."
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = os.listdir(WORK_DIR) if os.path.exists(WORK_DIR) else []
    if files:
        msg = "*Fichiers reçus :*\n" + "\n".join(f"• {f}" for f in files)
    else:
        msg = "*Aucun fichier reçu.*"
    await update.message.reply_text(msg)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Supprimer tous les fichiers reçus ? Répondez OUI pour confirmer."
    )
    context.user_data["clear_pending"] = True

async def confirm_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("clear_pending"):
        files = os.listdir(WORK_DIR)
        for f in files:
            os.remove(os.path.join(WORK_DIR, f))
        context.user_data["clear_pending"] = False
        await update.message.reply_text(f"✓ {len(files)} fichier(s) supprimé(s).")
    else:
        await update.message.reply_text("Aucune suppression en attente.")

# --- Gestion des messages textuels ---

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Commandes déjà traitées
    if text.startswith("/"):
        return

    # Analyse de la demande textuelle
    response = analyze_text_request(text)
    await update.message.reply_text(response, parse_mode="Markdown")

def analyze_text_request(text: str) -> str:
    """Analyse un message texte et produit une réponse FA2I appropriée."""

    text_lower = text.lower()

    # Détection des types de demande
    if any(kw in text_lower for kw in ["caption", "légende", "post"]):
        return generate_caption_request(text)

    if any(kw in text_lower for kw in ["hashtag", "hashtags"]):
        return generate_hashtags_request(text)

    if any(kw in text_lower for kw in ["script", "scénario", "histoire"]):
        return generate_script_request(text)

    if any(kw in text_lower for kw in ["storyboard", "plan de montage", "montage"]):
        return generate_montage_request(text)

    if any(kw in text_lower for kw in ["sous-titre", "sous-titres", "srt"]):
        return generate_subtitle_request(text)

    if any(kw in text_lower for kw in ["concept", "idée", "concept"]):
        return generate_concept_request(text)

    # Demande générale
    return (
        "Je viens de recevoir votre message. Pourriez-vous préciser :\n"
        "• Le type de contenu souhaité (caption, hashtags, script, storyboard, concept) ?\n"
        "• Le contexte de l'événement (nom, date, lieu, participants, objectif) ?\n\n"
        "Je produis le contenu dès que j'ai les informations."
    )

def generate_caption_request(text: str) -> str:
    return (
        "Pour produire une caption, j'ai besoin :\n"
        "• Du contexte de l'événement (nom, date, lieu)\n"
        "• Du message principal\n"
        "• De la plateforme cible\n\n"
        "Pouvez-vous me donner ces informations ?\n"
        "En attendant, voici un exemple de structure :\n\n"
        "🇮🇩 *Titre de l'événement*\n\n"
        "Description de l'événement...\n\n"
        "📍 Lieu, Date\n\n"
        "#Hashtags"
    )

def generate_hashtags_request(text: str) -> str:
    return (
        "Pour proposer des hashtags pertinents, j'ai besoin du contexte :\n"
        "• Événement / sujet\n"
        "• Plateforme cible\n"
        "• Public visé\n\n"
        "Exemple de catégories :\n"
        "• Organisation : #FA2I #FederationDesAssociationsIvoiriennesEnInde\n"
        "• Communauté : #IvoiriensEnInde #DiasporaIvoirienne #CommunautéIvoirienne\n"
        "• Lieu : #Inde #NewDelhi\n"
        "• Thématiques : #Unité #FiertéIvoirienne"
    )

def generate_script_request(text: str) -> str:
    return (
        "Pour produire un script, j'ai besoin :\n"
        "• Du contexte de l'événement\n"
        "• De l'objectif (informer, célébrer, promouvoir...)\n"
        "• De la durée cible\n"
        "• Des informations clés (invités, citations, chiffres)\n\n"
        "⚠️ Pour toute information non validée, j'utilise des placeholders.\n"
        "Pouvez-vous me donner les informations ?"
    )

def generate_montage_request(text: str) -> str:
    # Vérifier si FFmpeg est disponible
    ffmpeg_check = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if ffmpeg_check.returncode == 0:
        ffmpeg_status = "✅ FFmpeg est installé sur cette machine."
    else:
        ffmpeg_status = "⚠️ FFmpeg n'est pas installé. Installation : `sudo apt install ffmpeg` (Linux) ou téléchargement Windows."

    return (
        f"*Plan de montage — FA2I*\n\n"
        f"{ffmpeg_status}\n\n"
        "Voici la structure de travail :\n"
        "1. Concept + script\n"
        "2. Storyboard séquence par séquence\n"
        "3. Plan de montage FFmpeg (découper, assembler, textes, sous-titres, musique, export)\n"
        "4. Caption + hashtags\n\n"
        "Donnez-moi le contexte de l'événement et je produis le plan complet."
    )

def generate_subtitle_request(text: str) -> str:
    return (
        "Pour produire des sous-titres, j'ai besoin :\n"
        "• Du script ou du contenu textuel\n"
        "• De la langue (français par défaut, anglais sur demande)\n"
        "• Du timing souhaité\n\n"
        "Je génère le fichier SRT correspondant."
    )

def generate_concept_request(text: str) -> str:
    return (
        "Pour concevoir un concept vidéo, j'ai besoin :\n"
        "• Du contexte de l'événement\n"
        "• De l'objectif (informer, célébrer, promouvoir...)\n"
        "• De la plateforme cible\n"
        "• De la durée\n"
        "• Des informations clés\n\n"
        "Je produit : concept, hook, script, storyboard, plan de montage, textes à l'écran, voix-off, sous-titres, musique, caption, hashtags, format."
    )

# --- Gestion des photos ---

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # la plus grande résolution
    file = await context.bot.get_file(photo.file_id)

    # Générer un nom unique
    filename = f"photo_{update.message.date}_{photo.file_id}.jpg"
    filepath = os.path.join(WORK_DIR, filename)

    # Télécharger la photo
    await file.download_to_drive(filepath)

    # Analyser avec ffprobe
    analysis = analyze_photo_with_ffprobe(filepath)

    msg = (
        f"📸 *Photo reçue :* `{filename}`\n\n"
        f"*Métadonnées techniques :*\n"
        f"• Résolution : {analysis['width']} x {analysis['height']}\n"
        f"• Format : {analysis['format']}\n"
        f"• Taille : {analysis['size']}\n\n"
        f"*Contenu visuel :* Non analysé (vision_analyze non disponible)\n\n"
        f"⚠️ Pour le contenu de la photo, décrivez-moi ce qu'elle montre.\n"
        f"Je l'intégrerai dans le storyboard."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def analyze_photo_with_ffprobe(filepath: str) -> dict:
    """Analyser une image avec ffprobe — métadonnées uniquement."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", filepath],
        capture_output=True, text=True
    )
    import json
    data = json.loads(result.stdout)

    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})

    return {
        "width": stream.get("width", "?"),
        "height": stream.get("height", "?"),
        "format": stream.get("codec_name", "?"),
        "size": fmt.get("size", "?"),
        "duration": fmt.get("duration", "?"),
    }

# --- Gestion des vidéos (si reçues) ---

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    file = await context.bot.get_file(video.file_id)

    filename = f"video_{update.message.date}_{video.file_id}.mp4"
    filepath = os.path.join(WORK_DIR, filename)
    await file.download_to_drive(filepath)

    # Analyser avec ffprobe
    analysis = analyze_video_with_ffprobe(filepath)

    msg = (
        f"🎬 *Vidéo reçue :* `{filename}`\n\n"
        f"*Métadonnées techniques :*\n"
        f"• Résolution : {analysis['width']} x {analysis['height']}\n"
        f"• Durée : {analysis['duration']}s\n"
        f"• Codec vidéo : {analysis['video_codec']}\n"
        f"• Codec audio : {analysis['audio_codec']}\n"
        f"• Taille : {analysis['size']}\n\n"
        f"⚠️ Contenu visuel : à décrire par vous.\n"
        f"Je peux utiliser cette vidéo pour le montage si vous validez."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def analyze_video_with_ffprobe(filepath: str) -> dict:
    """Analyser une vidéo avec ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", filepath],
        capture_output=True, text=True
    )
    import json
    data = json.loads(result.stdout)

    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fmt = data.get("format", {})

    return {
        "width": video_stream.get("width", "?"),
        "height": video_stream.get("height", "?"),
        "duration": fmt.get("duration", "?"),
        "video_codec": video_stream.get("codec_name", "?"),
        "audio_codec": audio_stream.get("codec_name", "?"),
        "size": fmt.get("size", "?"),
    }

# --- Gestion des documents (fichiers divers) ---

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)

    filename = doc.file_name or f"document_{update.message.date}.dat"
    filepath = os.path.join(WORK_DIR, filename)
    await file.download_to_drive(filepath)

    msg = f"📄 *Document reçu :* `{filename}`\n\nTaille : {doc.file_size or '?'} octets."
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- Filtres de message ---

def get_handlers():
    """Retourne les handlers configurés pour le bot."""
    return [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("mode", mode_command),
        CommandHandler("auto_on", auto_on),
        CommandHandler("auto_off", auto_off),
        CommandHandler("status", status_command),
        CommandHandler("clear", clear_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
        MessageHandler(filters.PHOTO, handle_photo),
        MessageHandler(filters.VIDEO, handle_video),
        MessageHandler(filters.Document.ALL, handle_document),
    ]

# ============================================================
# POINT D'ENTRÉE DU BOT
# ============================================================

def main():
    """Lance le bot Telegram."""
    print(f"🟢 Lancement du bot FA2I Communication Agent...")
    print(f"   Token : {'*' * len(TOKEN)}")
    print(f"   Work dir : {WORK_DIR}")
    print()

    app = Application.builder().token(TOKEN).build()

    for handler in get_handlers():
        app.add_handler(handler)

    print("🟢 Bot en ligne — écoute des messages Telegram...")
    print("   /start pour commencer")
    print("   /help pour les commandes")
    print()

    try:
        app.run_polling()
    except TelegramError as e:
        print(f"❌ Erreur Telegram : {e}")
        exit(1)

if __name__ == "__main__":
    main()
