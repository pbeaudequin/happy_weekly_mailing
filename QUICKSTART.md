# Démarrage Rapide 🚀

Guide minimal pour démarrer en 5 minutes avec Happy Weekly Mailing.

## 1. Créer un mot de passe d'application Gmail

1. Aller sur https://myaccount.google.com/security
2. Activer la validation en 2 étapes (si ce n'est pas déjà fait)
3. Aller dans "Mots de passe des applications"
4. Créer un nouveau mot de passe pour "Mail"
5. Copier le mot de passe généré (vous en aurez besoin à l'étape suivante)

## 2. Configurer .netrc pour l'authentification Gmail

```bash
# Créer le fichier .netrc dans votre répertoire home
nano ~/.netrc
```

Ajouter ces lignes (remplacez par vos identifiants) :

```
machine smtp.gmail.com
  login votre.email@gmail.com
  password votre_mot_de_passe_application_gmail
```

**IMPORTANT** : Sauvegarder (Ctrl+O puis Ctrl+X) et protéger le fichier :

```bash
chmod 600 ~/.netrc
```

⚠️ **Le mot de passe ne doit JAMAIS être dans .env, seulement dans .netrc**

## 3. Créer le fichier .env

```bash
# Copier l'exemple
cp .env.example .env

# Éditer
nano .env
```

Configurez ces valeurs (**N'incluez PAS SMTP_USER et SMTP_PASSWORD**) :

```bash
# Configuration Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# Template email
EMAIL_TEMPLATE=design_classique

# Destinataires (OBLIGATOIRE - séparez les emails par des virgules)
TO_ADDRESSES=email1@example.com,email2@example.com

# Optionnel : période de récupération des événements (défaut : 14 jours)
DAYS_AHEAD=14
```

## 4. Tester le script

```bash
# Exécuter le script
uv run send-calendar

# Ou avec Python directement
uv run python -m happy_weekly_mailing.main
```

## 5. Automatiser avec cron (Optionnel)

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour un envoi tous les lundis à 9h
0 9 * * 1 cd /Users/philippe.beaudequin/dev/happy_weekly_mailing && /Users/philippe.beaudequin/.local/bin/uv run send-calendar >> /tmp/happy_mailing.log 2>&1
```

**Note** : Remplacez les chemins par vos chemins réels. Pour les trouver :
```bash
# Chemin du projet
pwd

# Chemin de uv
which uv
```

## 6. Automatiser avec GitHub Actions (Optionnel)

Le workflow `Send weekly mailing` envoie le mailing depuis GitHub Actions.

Dans les environnements GitHub `test` et `production`, configurez les secrets :

```bash
SMTP_USER
SMTP_PASSWORD
TO_ADDRESSES
```

Configurez aussi les variables non sensibles déjà présentes dans `.env.example` (`SMTP_HOST`, `SMTP_PORT`, `CALENDAR_ID`, `TIMEZONE`, etc.).

Pour tester manuellement : onglet **Actions** → **Send weekly mailing** → **Run workflow** → choisir `test`.

## Templates disponibles

Changez `EMAIL_TEMPLATE` dans `.env` :
- `design_classique` - Élégant avec tons marron/beige ⭐ (par défaut)
- `design_moderne` - Coloré avec dégradés violets
- `design_festif` - Joyeux avec ballons et émojis
- `design_minimaliste` - Épuré en noir et blanc

## Résolution de problèmes

### Aucun événement trouvé
- Vérifiez que le calendrier Google est public
- Changez `DAYS_AHEAD` dans `.env` (14 jours par défaut)

### Erreur d'authentification SMTP
- Vérifiez que le fichier `~/.netrc` existe et contient les bonnes informations
- Vérifiez les permissions du fichier `.netrc` : `chmod 600 ~/.netrc`
- Pour Gmail : utilisez un mot de passe d'application, pas votre mot de passe principal
- Le script indique dans sa sortie s'il utilise .netrc ou les variables d'environnement

### Le script ne trouve pas uv
Installez uv :
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Documentation complète

Consultez [README.md](README.md) pour la documentation détaillée.

---

Besoin d'aide ? Ouvrez une issue sur le projet ! 🆘
