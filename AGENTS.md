# Happy Weekly Mailing

Ce dépôt contient le script Python qui récupère les prochains événements du calendrier Google de Happy au Rouret et envoie un récapitulatif HTML par SMTP. Il récupère également les dernières publications de la photothèque du site public de l'association.

**Stack :** Python 3.11+, uv, `icalendar`, `requests`, SMTP, GitHub Actions
**Propriétaire :** non documenté dans le dépôt
**Ce que les agents peuvent faire :** modifier le code et exécuter les tests locaux ; l'envoi réel d'emails et l'accès au calendrier nécessitent une configuration et des secrets humains.

## Mise en place de l'environnement

- **Outils requis :** Python version indiquée dans `.python-version`, uv et un environnement réseau pour les appels Google Calendar et au site public.
- **Bootstrap :** `uv sync` depuis la racine du dépôt.
- **Dépendances locales :** aucune base de données, aucun service local ni conteneur requis pour les tests unitaires.
- **Fichiers d'environnement :** copier `.env.example` vers `.env`, puis renseigner les valeurs localement. Ne jamais versionner `.env` ni y stocker les identifiants SMTP.

### Actions nécessitant un humain

- Créer et protéger `~/.netrc` avec `chmod 600` pour l'authentification SMTP Gmail ; utiliser un mot de passe d'application, jamais le mot de passe principal.
- Configurer les secrets et variables des environnements GitHub Actions `test` et `production` avant de lancer le workflow d'envoi.
- Toute opération d'écriture sur le calendrier Google doit être explicitement confirmée par l'utilisateur avant exécution.

## Commandes

Depuis la racine du dépôt :

```bash
# Installer/synchroniser les dépendances
uv sync

# Exécuter les tests unitaires
uv run python -m unittest discover -s tests -v

# Exécuter le mailing
uv run send-calendar

# Alternative au point d'entrée déclaré dans pyproject.toml
uv run python -m happy_weekly_mailing.main
```

Le test de connexion SMTP documenté dans `README.md` nécessite une configuration SMTP valide et peut contacter un service externe. `pytest` n'est pas une dépendance déclarée ; utiliser la suite `unittest` ci-dessus.

## Definition of done

1. Les tests unitaires passent avec `uv run python -m unittest discover -s tests -v`.
2. Les templates HTML modifiés conservent les marqueurs et variables documentés dans `README.md`.
3. Les hooks de pré-commit, s'ils sont ajoutés ultérieurement au dépôt, doivent passer sur les fichiers modifiés et ne doivent jamais être ignorés.
4. Une modification de la configuration ou du lockfile est vérifiée avec `uv sync` et le fichier `uv.lock` est mis à jour seulement si nécessaire.

## Vocabulaire du domaine

- **Repas partagé :** événement généralement prévu de 12:30 à 14:30 à la Salle Galoubet.
- **Randonnée :** événement avec rendez-vous de covoiturage sur la place de la mairie du Rouret ; l'horaire par défaut est 09:00–16:00 sauf indication contraire dans le programme.
- **Orphelin :** événement présent dans Google Calendar mais absent de la page programme. Il doit être présenté à l'utilisateur et ne doit pas être supprimé automatiquement.

## Do not break

- La page programme publique est la source de vérité lors d'une synchronisation du calendrier ; ne pas inventer un événement absent de cette page.
- Ne jamais écrire dans Google Calendar sans présenter auparavant le diff (créations, mises à jour, événements inchangés et orphelins) et obtenir une confirmation explicite.
- Ne jamais supprimer automatiquement un événement orphelin. Demander séparément s'il faut le conserver ou le supprimer.
- Lors d'une mise à jour, préserver une description ou un lieu déjà renseigné manuellement si la page programme ne fournit pas une valeur explicite différente.
- Utiliser le fuseau `Europe/Paris` et des dates RFC3339 avec l'offset saisonnier correct (`+01:00` en hiver, `+02:00` en été). Vérifier les changements d'heure avant d'écrire.
- Une synchronisation doit être idempotente : comparer les événements par date de début et titre normalisé (minuscules, espaces et accents neutralisés) afin d'éviter les doublons.
- Ne pas envoyer d'invitations aux participants sans demande explicite ; ne jamais utiliser `--send-updates=all` par défaut.
- Ne jamais placer de mots de passe SMTP dans `.env`, le code, les logs ou GitHub Actions en clair. Utiliser `~/.netrc` localement ou les secrets GitHub.
- Le workflow GitHub Actions peut envoyer un email réel ; vérifier l'environnement choisi (`test` ou `production`) et les destinataires avant un lancement manuel.

## Conventions

- Les titres de calendrier utilisent des emojis cohérents avec le type : `🥾` pour les randonnées et `🍽️` pour les repas partagés. Les autres activités peuvent utiliser un emoji descriptif.
- Les descriptions des repas reprennent le texte standard documenté dans le skill de synchronisation ; les descriptions manuelles existantes sont prioritaires.
- Les templates disponibles sont `design_moderne`, `design_classique`, `design_festif` et `design_minimaliste`.
- Les variables de template et les marqueurs `EVENT_LOOP_START` / `EVENT_LOOP_END` sont documentés dans `README.md`.
- Le workflow CI/déploiement est `.github/workflows/send-weekly-mailing.yml`. Il installe avec `uv sync --frozen`, valide la configuration, puis exécute `uv run send-calendar`.
- Les titres et descriptions de pull requests doivent utiliser Conventional Commits et inclure une référence Jira lorsque le dépôt est intégré à ce processus. Aucun fichier CODEOWNERS ni ticket Jira par défaut n'est présent dans ce dépôt.

## Gotchas and tribal knowledge

- La page nommée `programme-2025-2026` peut afficher un programme `2026-2027`. Vérifier le titre et les années réellement affichés avant de déduire les dates.
- La pagination de `gog calendar events` est nécessaire (`--all-pages`) ; sans elle, des événements peuvent manquer et provoquer des créations en double.
- Les événements « toute la journée » utilisent des dates de fin exclusives avec `gog calendar create --all-day`.
- La photothèque est facultative : si le site est indisponible, le mailing doit continuer avec les événements du calendrier.
- Les dates d'été doivent conserver l'offset `+02:00`, tandis que les dates d'hiver utilisent `+01:00`; un mauvais offset décale l'heure affichée.

## Contexte approfondi

- Pour modifier le comportement du mailing, lire d'abord [README.md](README.md) et [QUICKSTART.md](QUICKSTART.md).
- Pour synchroniser le programme et Google Calendar, lire [.claude/skills/sync_cal/SKILL.md](.claude/skills/sync_cal/SKILL.md) avant toute opération d'écriture.
- Pour modifier les templates, consulter les quatre fichiers sous `templates/` et la section « Contribution » de `README.md`.
- Pour modifier l'automatisation, consulter [.github/workflows/send-weekly-mailing.yml](.github/workflows/send-weekly-mailing.yml).

## Maintenir ce fichier exact

- Si une commande échoue, qu'un chemin change ou que le comportement du dépôt évolue, corriger cette instruction dans le même changement et indiquer la preuve dans le message ou la description de PR.
- Appliquer cette règle à toutes les sections, notamment « Do not break » et « Gotchas and tribal knowledge ».
