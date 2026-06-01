# 💖 Duovrai Backend - Analyse de Compatibilité Amoureuse

Duovrai est une application B2C standalone proposant des rapports d'analyses de compatibilité amoureuse personnalisées de 8 à 12 pages. Les rapports sont rédigés par l'intelligence artificielle Claude (Anthropic API), mis en page de manière haut de gamme et exportés au format PDF via **WeasyPrint**, puis livrés automatiquement par e-mail après règlement sécurisé par **Stripe Checkout**.

---

## 🛠️ Stack Technique

* **Framework :** FastAPI (Python 3.11+)
* **Moteur PDF :** WeasyPrint (conversion HTML/CSS premium vers PDF imprimable)
* **Base de données :** SQLAlchemy (SQLite pour le développement, PostgreSQL pour la production) + Alembic
* **Passerelle de paiement :** Stripe Checkout (Hosted flow, Webhooks sécurisés)
* **Intelligence Artificielle :** Claude API (Anthropic client, prompts sophistiqués pour analyses denses)
* **Envoi d'e-mails :** `aiosmtplib` (SMTP Asynchrone avec attachements PDF)

---

## 📁 Architecture du Projet

Le projet adopte une architecture modulaire et scalable basée sur le Repository Pattern :

```
duovrai-backend/
├── alembic/                 # Scripts et environnements de migration de BDD
├── app/
│   ├── api/                 # Endpoints FastAPI
│   │   └── v1/
│   │       ├── stripe.py    # Tunnel de paiement et webhook Stripe
│   │       └── reports.py   # Téléchargement et statuts des rapports
│   ├── core/                # Fichiers de configuration globale (Pydantic Settings)
│   ├── database/            # Initialisation du moteur et sessions de BDD
│   ├── middleware/          # Middlewares personnalisés (CORS, logs, exceptions)
│   ├── models/              # Modèles SQLAlchemy (Order, CompatibilityReport)
│   ├── repositories/        # Abstraction de la base de données (Repository Pattern)
│   ├── schemas/             # Modèles de validation des données Pydantic
│   ├── services/            # Logique métier (Stripe, Claude, WeasyPrint, Email)
│   ├── templates/           # Templates HTML/CSS premium pour WeasyPrint
│   ├── types/               # Enums et types personnalisés (ex: OrderStatus)
│   ├── tests/               # Tests unitaires et d'intégration (pytest)
│   ├── main.py              # Point d'entrée de l'application FastAPI
│   └── seed.py              # Script de pré-remplissage des données de test
├── .env.example             # Exemple de variables d'environnement requis
├── .gitignore               # Configuration d'exclusion Git
├── alembic.ini              # Fichier de configuration Alembic
├── docker-compose.yml       # Orchestration locale (App + PostgreSQL)
├── Dockerfile               # Recette de conteneurisation optimisée pour WeasyPrint
├── pytest.ini               # Paramètres de test Pytest
└── requirements.txt         # Dépendances Python requises
```

---

## 🚀 Démarrage Rapide

### Option A : Lancement via Docker (Recommandé)

Docker installe automatiquement toutes les dépendances système de WeasyPrint (comme Pango/GTK) sous Linux. C'est la méthode la plus rapide et la plus fiable.

1. Clonez le dépôt et copiez la configuration :
   ```bash
   cp .env.example .env
   ```
2. Lancez le projet :
   ```bash
   docker-compose up --build
   ```
3. L'API est disponible à l'adresse : [http://localhost:8000](http://localhost:8000) (Swagger à `/docs`).

### Option B : Installation Locale (Développement)

#### 1. Prérequis pour WeasyPrint (Windows)
WeasyPrint nécessite l'installation des bibliothèques système **GTK+** pour compiler les polices et polir les PDFs sous Windows.
1. Téléchargez et exécutez le package d'installation de GTK+ pour Windows (ex: via [MSYS2](https://www.msys2.org/) ou le build direct [GTK for Windows](https://github.com/tschoonj/GTK-for-Windows-installer/releases)).
2. Assurez-vous que le chemin du dossier `bin/` de GTK est ajouté dans votre variable d'environnement `PATH` système.

*Note : Si GTK n'est pas présent lors du lancement local, le serveur s'activera tout de même en activant automatiquement un générateur PDF simulé (Mock PDF) pour éviter de crasher le serveur de test.*

#### 2. Lancement
1. Créez un environnement virtuel et installez les dépendances :
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Lancez le serveur :
   ```bash
   uvicorn app.main:app --reload
   ```
3. Pré-remplissez la base de données avec des flux de tests :
   ```bash
   python app/seed.py
   ```

---

## 🧪 Simulation Complète du Tunnel (Mock Mode)

Le projet intègre un **Stripe Mock Mode** et un **Claude Mock Mode** pour tester l'intégralité du tunnel d'achat et de génération sans configurer de clés API payantes !

1. Lancez le serveur localement ou sur Docker.
2. Créez une commande en envoyant une requête `POST` sur `/api/v1/stripe/checkout` :
   ```json
   {
     "email": "test-client@example.com",
     "partner1_name": "Valentin",
     "partner1_birthdate": "1994-06-15",
     "partner2_name": "Léa",
     "partner2_birthdate": "1996-09-08",
     "plan_type": "PREMIUM"
   }
   ```
3. L'API renvoie un ID de session et un `checkout_url`. Puisque nous sommes en Mock Mode, ouvrez ce lien dans votre navigateur. Il pointera vers notre routeur de simulation :
   `http://localhost:8000/api/v1/stripe/mock-checkout-success?session_id=cs_test_xxx`
4. Cette route déclenche instantanément le webhook en arrière-plan (Background Task) qui :
   * Valide le paiement simulé.
   * Génère l'analyse amoureuse (via Claude en mock ou en réel).
   * Compile les 8 à 12 pages avec WeasyPrint et crée le PDF.
   * Simule l'envoi de l'e-mail avec la pièce jointe.
5. Suivez l'état ou téléchargez le PDF de test en appelant :
   `http://localhost:8000/api/v1/reports/{order_id}/download`

---

## 🔒 Sécurité du Webhook Stripe

En production, le webhook Stripe valide rigoureusement la signature cryptographique envoyée par Stripe :
```python
stripe.webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
```
Toute signature falsifiée ou altérée lèvera une erreur `400 Bad Request`, empêchant les fraudes sur la génération gratuite de rapports amoureux payants.
