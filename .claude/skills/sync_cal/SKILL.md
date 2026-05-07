---
name: sync_cal
description: Use when the user wants to synchronize the Happy au Rouret programme table (https://www.happy-au-rouret.fr/programme-2025-2026) with the Happy au Rouret Google Calendar (happy.rouret@gmail.com). Triggers include "sync cal", "synchronise le calendrier", "mettre à jour le calendrier Happy", "/sync_cal".
---

# sync_cal - Synchronise programme Happy au Rouret avec Google Calendar

## Objectif

Synchroniser la table publiée sur https://www.happy-au-rouret.fr/programme-2025-2026 avec le Google Calendar `happy.rouret@gmail.com`.

La source de vérité est **la page web**. Le calendrier doit refléter la table.

## Outils requis

- `WebFetch` pour lire la page programme
- CLI `gog` (déjà installée, accès en write sur le calendrier `happy.rouret@gmail.com`)

## Defaults (à appliquer sauf indication contraire dans la table)

### Repas partagé
- **Horaire**: 12:30 -> 14:30 (heure locale Europe/Paris)
- **Lieu**: Salle Galoubet, Le Rouret, France
- **Description**: "Repas partagé Happy au Rouret. Le but est de se réunir et que chacun amène un plat. L'organisation des plats (entrées, plats, desserts, boissons) se fait sur le fil WhatsApp pour bien équilibrer le repas."

### Randonnée
- **Rendez-vous**: 9:00 - 9:30 sur la place de la mairie du Rouret pour covoiturage
- **Lieu (Calendar)**: Place de la Mairie, Le Rouret, France (point de RDV covoiturage)
- **Description**: "Randonnée Happy au Rouret. Rendez-vous entre 9h et 9h30 sur la place de la mairie du Rouret pour covoiturer jusqu'au lieu de départ. [destination/détails de la table]"
- **Horaire**: 9:00 a 16:00 par defaut (sauf indication contraire dans la table).

### Autres événements
- Reprendre les infos de la table telles quelles. Demander confirmation si une info clé manque (heure, lieu).

## Workflow

```
1. Lire la table        -> WebFetch la page programme
2. Lire le calendrier   -> gog calendar events happy.rouret@gmail.com --from <today> --to <fin de saison> --all-pages -j
3. Faire le diff        -> par titre + date (clé de matching)
4. Présenter le recap   -> à créer / à mettre à jour / inchangés / orphelins (présents dans cal mais absents de la table)
5. Demander confirmation
6. Appliquer            -> gog calendar create / update
7. Recap final
```

### Étape 1 - Lire la table

```
WebFetch url=https://www.happy-au-rouret.fr/programme-2025-2026
prompt="Extrait tous les événements du programme sous forme structurée: date, titre, type (repas partagé / randonnée / autre), heure si précisée, lieu si précisé, description/notes. Préserve l'ordre chronologique."
```

### Étape 2 - Lire le calendrier existant

```bash
gog calendar events happy.rouret@gmail.com \
  --from $(date +%Y-%m-%d) \
  --to 2026-08-31 \
  --all-pages \
  -j
```

Conserver `id`, `summary`, `start`, `end`, `location`, `description` pour chaque événement.

### Étape 3 - Matching

Pour chaque événement de la table:
- Cherche dans le calendrier un event dont la **date de début** correspond ET le **titre** est similaire (insensible à la casse, espaces, accents).
- Match trouvé -> comparer champs (heure, lieu, description). Si différent -> UPDATE (avec règle de préservation ci-dessous). Sinon -> INCHANGE.
- Pas de match -> CREATE.

Pour chaque event du calendrier sans correspondance dans la table:
- Marquer ORPHELIN. **Ne pas supprimer automatiquement** - le présenter à l'utilisateur qui décidera.

**Règle de préservation du contenu manuel**: si l'event existant possède déjà une `description` non vide, **la conserver telle quelle** - elle a probablement été saisie manuellement par un membre. Ne jamais l'écraser avec la description par défaut. Idem pour le `location`: si le calendrier a déjà une valeur et que la table n'en précise pas une différente, garder l'existante.

En pratique, lors d'un UPDATE:
- Mettre à jour uniquement les champs où la table apporte une info **explicite et différente** de l'existant.
- Si la table ne dit rien sur un champ et que l'event existant a déjà du contenu -> ne pas toucher ce champ.
- Si l'event existant n'a rien (champ vide) -> remplir avec le default du skill.

### Étape 4 - Recap (avant toute action)

Format obligatoire:

```
## Recap synchronisation calendrier Happy au Rouret

### A créer (N événements)
- [DATE] [TITRE] - [HORAIRE] @ [LIEU]
  Description: [extrait]

### A mettre à jour (N événements)
- [DATE] [TITRE]
  - Champ "X": "ancien" -> "nouveau"

### Inchangés (N événements)
- [DATE] [TITRE]

### Orphelins dans le calendrier (N événements - non listés sur la page)
- [DATE] [TITRE] - id: [eventId]
  Action proposée: garder / supprimer (à confirmer)
```

### Étape 5 - Confirmation utilisateur

Toujours demander une confirmation explicite avant d'écrire dans le calendrier. Utiliser `AskUserQuestion` ou attendre un "ok" / "go" / "vas-y" en français.

Pour les orphelins, demander explicitement quoi faire (garder vs supprimer).

### Étape 6 - Application

**Création**:
```bash
gog calendar create happy.rouret@gmail.com \
  --summary "Repas partagé" \
  --from "2026-01-12T12:30:00+01:00" \
  --to "2026-01-12T14:30:00+01:00" \
  --location "Salle Galoubet, Le Rouret, France" \
  --description "Repas partagé Happy au Rouret. Le but est de se réunir et que chacun amène un plat. L'organisation des plats (entrées, plats, desserts, boissons) se fait sur le fil WhatsApp pour bien équilibrer le repas." \
  -j
```

**Mise à jour**:
```bash
gog calendar update happy.rouret@gmail.com <eventId> \
  --from "..." --to "..." --location "..." --description "..."
```

**Suppression** (orphelins, uniquement si confirmé):
```bash
gog calendar delete happy.rouret@gmail.com <eventId> -y
```

### Étape 7 - Recap final

Lister succinctement ce qui a été créé / mis à jour / supprimé, avec les IDs renvoyés par gog.

## Règles importantes

- **Fuseau horaire**: toujours Europe/Paris. Utiliser le format RFC3339 avec offset (`+01:00` en hiver, `+02:00` en été).
- **Idempotence**: relancer le skill ne doit rien changer si la table et le calendrier sont déjà synchro.
- **Pas de suppression auto**: les orphelins exigent toujours confirmation utilisateur.
- **Dry-run disponible**: si l'utilisateur dit "dry-run" / "à blanc", ajouter `-n` à toutes les commandes `gog`.
- **Jamais de `--send-updates=all`**: pas d'invitations email aux invités sans demande explicite.

## Erreurs fréquentes à éviter

| Erreur | Correction |
|--------|------------|
| Créer en doublon car le titre a une casse différente | Comparer en lowercase + trim + sans accents |
| Décaler l'heure d'1h | Bien mettre `+01:00` ou `+02:00` selon DST |
| Supprimer un event sans confirmation | Toujours lister les orphelins et demander |
| Oublier `--all-pages` sur `events list` | Sinon on rate les events au-delà du 10e |
| Écraser une description/lieu saisi manuellement par les défauts du skill | Toujours préserver le contenu non vide existant - voir "Règle de préservation du contenu manuel" |

## Quand ne pas utiliser ce skill

- Si l'utilisateur veut juste lire le calendrier (pas de modif) -> utiliser `gog calendar events` directement.
- Si l'utilisateur veut modifier un seul event ponctuel -> utiliser `gog calendar update` directement.
- Si la source des events n'est pas la page programme (ex: notes manuscrites, autre site) -> ne pas utiliser ce skill, ses defaults ne s'appliquent pas.
