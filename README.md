# FA2I Telegram Bot

Bot Telegram pour la **Fédération des Associations Ivoiriennes en Inde (FA2I)**.

## Description

Bot Telegram permettant de recevoir et gérer les fichiers média (photos/vidéos) envoyés par la communauté FA2I.

## Structure du projet

```
fa2i-telegram-bot/
├── bot.py              # Code principal du bot
├── token.txt           # Token du bot (NON inclus - secret)
├── received_files/    # Fichiers reçus (non inclus)
└── .gitignore
```

## Sécurité

- `token.txt` est ignoré par Git (`.gitignore`) — le token n'est jamais commité
- `received_files/` est ignoré — les fichiers reçus ne sont pas versionés

## Installation

```bash
pip install python-telegram-bot
```

## Démarrage

1. Créer un fichier `token.txt` avec le token du bot Telegram
2. Lancer le bot :
```bash
python bot.py
```

## Licence

MIT — FA2I Secrétariat Communication
