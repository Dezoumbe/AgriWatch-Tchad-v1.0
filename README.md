# AgriWatch Tchad — Guide d'installation et de build

## Fichiers du projet
```
agriwatch/
├── main.py          ← Code source principal
├── build.bat        ← Script de compilation Windows (.exe)
├── requirements.txt ← Dépendances Python
└── README.md        ← Ce fichier
```

## Prérequis
- Python 3.10 ou supérieur → https://www.python.org/downloads/
- pip (inclus avec Python)

## Étape 1 — Installer les dépendances
```bash
pip install customtkinter pyinstaller
```

## Étape 2 — Lancer en mode développement
```bash
python main.py
```

## Étape 3 — Compiler le .exe
Double-cliquer sur `build.bat`  
OU depuis le terminal :
```bash
pyinstaller --onefile --windowed --name "AgriWatch_Tchad" main.py
```
Le fichier `.exe` sera dans le dossier `dist/`

## Structure de la base de données (SQLite)
- `parcelles`     — toutes les parcelles agricoles
- `rendements`    — données de production par campagne
- `alertes`       — historique des SMS et alertes
- `observations`  — notes de terrain par parcelle
- `utilisateurs`  — agents, agriculteurs, admins

## Fonctionnalités incluses
✅ Tableau de bord avec métriques en temps réel  
✅ Gestion complète des parcelles (CRUD)  
✅ Suivi des rendements par culture et campagne  
✅ Envoi et historique des alertes SMS  
✅ Gestion des utilisateurs et agents  
✅ Base de données locale SQLite (aucun serveur requis)  
✅ Interface sombre moderne (CustomTkinter)  

## Prochaines évolutions possibles
- Intégration API météo (OpenWeatherMap)
- Export PDF/Excel des rapports
- Module cartographique (Leaflet via webview)
- Synchronisation cloud (PostgreSQL distant)
- Version Android (Kivy ou Flutter)

## Auteur
Dezoumbe Ouahdabe Innocent — Centre COBRA, Abéché
Ingénieur Big Data, chef de projet AgriWatch Tchad
