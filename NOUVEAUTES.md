# 🎨 Nouveautés - Style Winamp Professionnel

## 🚀 Améliorations de Visualize

Ce document décrit toutes les améliorations apportées pour un style **Winamp professionnel**.

---

## ✨ Nouveaux Effets Visuels

### 🎚️ **Spectrum Effect** (`spectrum`)
- **Description** : Spectre circulaire inspiré de l'effet classique de Winamp
- **Caractéristiques** :
  - 32 bandes de fréquence disposées en cercle
  - Rotation synchronisée avec le BPM
  - Pics qui restent brièvement (peak hold)
  - Cœur central qui pulse au rythme de la musique
  - Cercles concentriques de fond
  - Réaction en temps réel au volume et aux fréquences

**Parfait pour** : Un look rétro Winamp authentique

---

### 🔮 **Plasma Effect** (`plasma`)
- **Description** : Effet plasma psychédélique fluide avec distorsions organiques
- **Caractéristiques** :
  - Motifs de plasma générés mathématiquement
  - 20 points de contrôle dynamiques
  - Réaction aux beats, volume et BPM
  - Distorsion radiale et spiralée
  - Cercles pulsants et lignes radiales
  - Vignette pour un effet professionnel

**Parfait pour** : Des visualisations hypnotiques et fluides

---

## 🎨 Effets Améliorés

### 📊 **Bar Effect** (`bars`)
**Nouveautés** :
- ✅ **Peak Hold** : Les pics restent visibles brièvement après le beat
- ✅ **Bords lumineux** : Contour brillant autour des barres
- ✅ **Dégradé vertical** : Les barres s'estompent vers le haut
- ✅ **Pulsation globale** : Les barres réagissent au volume global
- ✅ **Boost des basses** : Les premières barres (basses) ont plus d'amplitude
- ✅ **64 barres** : Plus de détails pour une meilleure résolution

**Style** : Égaliseur audio classique avec des améliorations modernes

---

## 🎨 Nouvelles Palettes de Couleurs

### 💚 **Winamp Classic** (`winamp_classic`)
- **Couleurs** :
  - Vert vif (0, 255, 0)
  - Vert moyen (0, 200, 0)
  - Vert sombre (0, 180, 0)
  - Vert foncé (0, 128, 0)
  - Jaune vif (255, 255, 0)
  - Jaune moyen (200, 200, 0)
  - Jaune foncé (150, 150, 0)

**Utilisation** : Pour un look authentique des années 90

---

## 🎯 Configuration Recommandée pour un Style Winamp

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Effet** | `spectrum` ou `bars` | Les plus proches du style Winamp |
| **Palette** | `winamp_classic` | Vert et jaune authentiques |
| **Présélection** | `normal` ou `high` | Meilleure qualité |
| **Résolution** | `1080p` ou `1440p` | Pour un rendu net |

---

## 📊 Liste Complète des Effets Disponibles

| Effet | Description | Nouveau/Amélioré |
|-------|-------------|------------------|
| `random` | Choix aléatoire | - |
| `bars` | Barres de fréquence (égaliseur) | ✅ **Amélioré** |
| `circles` | Cercles concentriques pulsants | - |
| `particles` | Particules qui réagissent au son | - |
| `tunnel` | Tunnel psychédélique avec distorsion | - |
| `wave` | Vagues concentriques | - |
| `spectrum` | Spectre circulaire style Winamp | ✅ **Nouveau** |
| `plasma` | Plasma psychédélique fluide | ✅ **Nouveau** |

---

## 🎨 Liste Complète des Palettes Disponibles

| Palette | Description |
|---------|-------------|
| `psychedelic` | Couleurs vives (magenta, cyan, jaune, etc.) |
| `retro` | Style rétro avec vert, jaune, bleu |
| `winamp_classic` | **Nouveau**: Vert et jaune classiques de Winamp |
| `dark` | Couleurs sombres pour fond noir |
| `rainbow` | Dégradé d'arc-en-ciel |

---

## 🚀 Utilisation en Ligne de Commande

### Export avec les nouveaux effets

```bash
# Export avec le spectre circulaire
make run-cli AUDIO=ma_musique.mp3 OUTPUT=video.mp4 EFFECT=spectrum COLOR=winamp_classic PRESET=normal

# Export avec les barres améliorées
make run-cli AUDIO=ma_musique.mp3 OUTPUT=video.mp4 EFFECT=bars COLOR=winamp_classic PRESET=high

# Export rapide pour test
make run-cli AUDIO=test.mp3 OUTPUT=test.mp4 EFFECT=plasma PRESET=dev
```

### Options disponibles

```bash
EFFECT=random|bars|circles|particles|tunnel|wave|spectrum|plasma
COLOR=psychedelic|retro|winamp_classic|dark|rainbow
PRESET=dev|fast|normal|high|4k
```

---

## 💡 Conseils pour de Meilleurs Résultats

1. **Pour un style Winamp authentique** :
   ```
   Effet: spectrum
   Palette: winamp_classic
   Preset: normal
   ```

2. **Pour des visualisations fluides** :
   ```
   Effet: plasma
   Palette: psychedelic ou rainbow
   Preset: normal ou high
   ```

3. **Pour un égaliseur classique** :
   ```
   Effet: bars
   Palette: winamp_classic ou retro
   Preset: normal
   ```

4. **Pour des tests rapides** :
   ```
   Preset: dev ou fast
   ```

---

## 🔧 Fonctionnalités Techniques

### Synchronisation Audio

Tous les effets réagissent maintenant à :
- **Volume** : Intensité globale
- **Bandes de fréquence** : 16 bandes pour une analyse fine
- **Bass/Mids/Treble** : Répartition spectrale
- **BPM** : Vitesse de rotation et pulsation
- **Beats** : Détection des temps forts
- **Beat Strength** : Intensité des beats

### Peak Hold

L'effet `bars` implémente maintenant un système de **peak hold** :
- Les pics des barres restent visibles pendant 1 seconde
- Les pics s'estompent progressivement
- Visualisation plus facile des maxima

### Rotation BPM

L'effet `spectrum` synchronise sa rotation avec le BPM :
- Plus le BPM est élevé, plus ça tourne vite
- La rotation est fluide et naturelle
- Synchronisation parfaite avec la musique

---

## 📚 Historique des Améliorations

| Date | Version | Changements |
|------|---------|-------------|
| 2026-06-21 | v2.0 | Ajout des effets spectrum et plasma, amélioration de bars, palette winamp_classic |

---

## 🎵 Exemples de Combinaisons

### Combinaison 1: Winamp Classic
```
Effet: spectrum
Palette: winamp_classic
Preset: normal
→ Résultat: Spectre circulaire vert/jaune qui tourne au rythme de la musique
```

### Combinaison 2: Égaliseur Moderne
```
Effet: bars
Palette: winamp_classic
Preset: high
→ Résultat: Barres avec peak hold, style égaliseur pro
```

### Combinaison 3: Psychédélique Fluide
```
Effet: plasma
Palette: rainbow
Preset: normal
→ Résultat: Plasma coloré avec distorsions dynamiques
```

### Combinaison 4: Tunnel Hypnotique
```
Effet: tunnel
Palette: psychedelic
Preset: high
→ Résultat: Tunnel 3D avec distorsions complexes
```

---

## 🤝 Remerciements

Ces améliorations ont été inspirées par :
- Le visualiseur classique de **Winamp**
- Les effets psychédéliques des années 90
- Les visualisations modernes de musique

---

*Document généré automatiquement - Dernière mise à jour: 2026-06-21*