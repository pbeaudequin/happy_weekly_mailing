# Happy Weekly Mailing 📧

Script Python automatisé pour envoyer des emails récapitulatifs des prochains événements du calendrier Happy au Rouret.

## 📋 Description

Ce script récupère automatiquement les événements du calendrier Google de l'association Happy au Rouret et envoie un email HTML élégant aux membres avec le récapitulatif des prochains rendez-vous.

**Happy au Rouret** est une association locale qui favorise les échanges entre Rourétans et cimente les liens intergénérationnels à travers diverses activités : repas partagés, randonnées, jardin collectif, sorties culturelles, etc.

## ✨ Fonctionnalités

- 📅 Récupération automatique des événements depuis Google Calendar
- 🌐 Mise en avant des 3 dernières publications de la photothèque Happy au Rouret
- 🎨 4 designs d'email au choix (moderne, classique, festif, minimaliste)
- 📧 Envoi d'emails HTML professionnels
- ⏰ Compatible avec l'exécution automatique via cron
- 🔒 Configuration sécurisée via variables d'environnement
- 🌍 Support des fuseaux horaires et événements "toute la journée"

## 🚀 Installation

### Prérequis

- Python 3.11 ou supérieur
- [uv](https://github.com/astral-sh/uv) - Gestionnaire de paquets Python ultra-rapide

### Installer uv

```bash
# macOS et Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation du projet

```bash
# Cloner ou télécharger le projet
cd happy_weekly_mailing

# Synchroniser les dépendances avec uv
uv sync
```

## ⚙️ Configuration

### 1. Créer le fichier de configuration

Copier le fichier d'exemple et le personnaliser :

```bash
cp .env.example .env
```

### 2. Configurer les variables d'environnement

Éditer le fichier `.env` avec vos paramètres :

```bash
# Configuration du calendrier
CALENDAR_ID=happy.rouret@gmail.com
TIMEZONE=Europe/Paris
DAYS_AHEAD=14

# Template d'email (design_classique recommandé)
EMAIL_TEMPLATE=design_classique
EMAIL_SUBJECT=Happy au Rouret - Prochains événements
FROM_NAME=Happy au Rouret

# Récapitulatif du site Happy au Rouret
WEBSITE_RECAP_ENABLED=true
WEBSITE_RECAP_BASE_URL=https://www.happy-au-rouret.fr
WEBSITE_RECAP_YEAR=
WEBSITE_RECAP_LIMIT=3

# Configuration SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe
SMTP_USE_TLS=true

# Destinataires
TO_ADDRESSES=membre1@example.com,membre2@example.com
```

### 3. Configuration SMTP avec .netrc 🔐

Les identifiants Gmail sont stockés de manière sécurisée dans le fichier `.netrc`, qui est une méthode standard Unix pour gérer les authentifications.

**Pourquoi .netrc ?**
- ✅ Plus sécurisé (permissions restrictives `chmod 600`)
- ✅ Les mots de passe ne sont jamais dans git ou dans `.env`
- ✅ Standard Unix supporté par de nombreux outils
- ✅ Séparation claire entre configuration et secrets

#### Configuration Gmail avec .netrc

**Étape 1 : Créer un mot de passe d'application Gmail**

1. Aller sur https://myaccount.google.com/security
2. Activer la validation en 2 étapes (si ce n'est pas déjà fait)
3. Aller dans "Mots de passe des applications"
4. Créer un nouveau mot de passe pour "Mail"
5. Copier le mot de passe généré

**Étape 2 : Créer le fichier .netrc**

```bash
# Copier l'exemple
cp .netrc.example ~/.netrc

# Éditer avec vos identifiants
nano ~/.netrc
```

**Étape 3 : Contenu du fichier `~/.netrc`**

```
machine smtp.gmail.com
  login votre.email@gmail.com
  password votre_mot_de_passe_application
```

**Étape 4 : Protéger le fichier (OBLIGATOIRE)**

```bash
chmod 600 ~/.netrc
```

**Étape 5 : Configurer .env (sans identifiants)**

Dans votre `.env`, configurez uniquement le serveur et les destinataires :

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
TO_ADDRESSES=membre1@example.com,membre2@example.com
```

⚠️ **IMPORTANT : Ne mettez JAMAIS `SMTP_USER` et `SMTP_PASSWORD` dans `.env`**

#### Autres fournisseurs SMTP

La méthode `.netrc` fonctionne avec tous les serveurs SMTP (OVH, Office 365, etc.). Changez simplement `machine smtp.gmail.com` par votre serveur SMTP dans `~/.netrc`, et configurez `SMTP_HOST` dans `.env` en conséquence.

## 🎨 Templates d'email disponibles

Le projet inclut 4 designs différents :

1. **design_moderne** - Design coloré avec dégradés violets et cartes visuelles modernes
2. **design_classique** ⭐ - Design élégant avec tons marron/beige, style traditionnel
3. **design_festif** - Design joyeux et coloré avec ballons et émojis
4. **design_minimaliste** - Design épuré et professionnel en noir et blanc

Pour changer de template, modifier la variable `EMAIL_TEMPLATE` dans `.env`.

## 🌐 Récapitulatif du site

Par défaut, l'email ajoute dans l'introduction les 3 dernières publications de la photothèque du site Happy au Rouret.

Configuration disponible dans `.env` :

```bash
# Activer ou désactiver la section
WEBSITE_RECAP_ENABLED=true

# Site à consulter
WEBSITE_RECAP_BASE_URL=https://www.happy-au-rouret.fr

# Année à consulter. Laisser vide pour utiliser l'année courante.
WEBSITE_RECAP_YEAR=

# Nombre de publications à afficher
WEBSITE_RECAP_LIMIT=3
```

La page utilisée est `phototheque-{année}`. Par exemple, en 2026, le script consulte `https://www.happy-au-rouret.fr/phototheque-2026`.
Si le site est indisponible, l'email est quand même généré avec les événements du calendrier.

## 🏃 Utilisation

### Exécution manuelle

```bash
# Avec uv
uv run send-calendar

# Ou directement avec Python
uv run python -m happy_weekly_mailing.main
```

### Test de configuration

Pour tester votre configuration SMTP sans envoyer d'email :

```bash
uv run python -c "from happy_weekly_mailing.email_sender import EmailSender; from dotenv import load_dotenv; import os; load_dotenv(); EmailSender(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', '587')), os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD')).test_connection()"
```

## ⏰ Automatisation avec Cron

Pour envoyer automatiquement les emails de façon hebdomadaire ou quotidienne, configurer un cron job.

### Éditer le crontab

```bash
crontab -e
```

### Exemples de configuration

#### Envoi tous les lundis à 9h00

```cron
0 9 * * 1 cd /chemin/vers/happy_weekly_mailing && /chemin/vers/.local/bin/uv run send-calendar >> /tmp/happy_mailing.log 2>&1
```

#### Envoi tous les jours à 8h00

```cron
0 8 * * * cd /chemin/vers/happy_weekly_mailing && /chemin/vers/.local/bin/uv run send-calendar >> /tmp/happy_mailing.log 2>&1
```

#### Envoi le 1er et 15 de chaque mois à 10h00

```cron
0 10 1,15 * * cd /chemin/vers/happy_weekly_mailing && /chemin/vers/.local/bin/uv run send-calendar >> /tmp/happy_mailing.log 2>&1
```

### Trouver les chemins corrects

```bash
# Chemin vers uv
which uv

# Chemin absolu du projet
pwd
```

### Format cron

```
* * * * * commande
│ │ │ │ │
│ │ │ │ └─── Jour de la semaine (0-7, 0 et 7 = dimanche)
│ │ │ └───── Mois (1-12)
│ │ └─────── Jour du mois (1-31)
│ └───────── Heure (0-23)
└─────────── Minute (0-59)
```

### Vérifier les logs

```bash
tail -f /tmp/happy_mailing.log
```

## 📁 Structure du projet

```
happy_weekly_mailing/
├── happy_weekly_mailing/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée principal
│   ├── calendar_fetcher.py  # Récupération des événements
│   ├── website_recap_fetcher.py # Récupération des dernières publications du site
│   ├── email_generator.py   # Génération des emails HTML
│   └── email_sender.py      # Envoi des emails via SMTP
├── templates/
│   ├── design_moderne.html
│   ├── design_classique.html
│   ├── design_festif.html
│   └── design_minimaliste.html
├── .env                     # Configuration (à créer)
├── .env.example             # Exemple de configuration
├── pyproject.toml           # Configuration du projet
└── README.md                # Ce fichier
```

## 🔧 Dépannage

### Aucun événement trouvé

- Vérifier que le calendrier est public
- Vérifier l'ID du calendrier dans `.env`
- Vérifier qu'il y a bien des événements dans la période (DAYS_AHEAD)

### Pas de publications du site dans l'email

- Vérifier que `WEBSITE_RECAP_ENABLED=true`
- Vérifier que la page `phototheque-{année}` existe sur le site
- Renseigner `WEBSITE_RECAP_YEAR=2026` pour forcer une année précise
- Le script continue sans bloquer l'envoi si le site est temporairement indisponible

### Erreur d'authentification SMTP

- Pour Gmail, vérifier que vous utilisez un mot de passe d'application
- Vérifier les identifiants SMTP
- Vérifier que le port et le mode TLS sont corrects

### Erreur de template

- Vérifier que le nom du template dans `.env` est correct
- Les templates disponibles : design_moderne, design_classique, design_festif, design_minimaliste

### Le cron ne s'exécute pas

- Vérifier les chemins absolus dans le crontab
- Vérifier les permissions d'exécution
- Consulter les logs système : `grep CRON /var/log/syslog` (Linux) ou `log show --predicate 'process == "cron"' --last 1h` (macOS)

## 🤝 Contribution

Pour modifier les templates ou ajouter de nouvelles fonctionnalités :

1. Les templates HTML sont dans `templates/`
2. Utiliser les marqueurs `{variable}` pour les données dynamiques
3. Encadrer la section des événements avec `<!-- EVENT_LOOP_START -->` et `<!-- EVENT_LOOP_END -->`

Variables disponibles pour les templates :
- `{day}` - Jour du mois (ex: "15")
- `{month}` - Mois en français (ex: "Janvier")
- `{month_short}` - Mois court (ex: "Jan")
- `{time}` - Heure formatée (ex: "14:00 - 16:00")
- `{title}` - Titre de l'événement
- `{location}` - Lieu de l'événement
- `{description}` - Description HTML (peut être vide)
- `{event_color}` - Couleur de l'événement (hex)
- `{icon}` - Émoji d'icône

## 📄 Licence

Ce projet est développé pour l'association Happy au Rouret.

## 🔗 Liens utiles

- Site web : https://www.happy-au-rouret.fr/
- Documentation uv : https://docs.astral.sh/uv/
- Calendrier Google : https://calendar.google.com/calendar/embed?src=happy.rouret%40gmail.com

---

Développé avec ❤️ pour Happy au Rouret
