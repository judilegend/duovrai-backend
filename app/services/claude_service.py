import logging
import anthropic
from app.core.config import settings
from app.models.models import Order
from app.types.enums import PlanType

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        # Initialize Anthropic Client
        self.client = None
        if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("sk-ant-api03-dummy"):
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def is_mock_enabled(self) -> bool:
        return self.client is None

    def generate_love_analysis(self, order: Order) -> str:
        """
        Generates a deep, rich romantic compatibility report using Anthropic Claude API.
        Tailored based on whether they chose the 'ESSENTIEL' or 'PREMIUM' plan.
        """
        p1_name = order.partner1_name
        p1_birth = order.partner1_birthdate
        p2_name = order.partner2_name
        p2_birth = order.partner2_birthdate
        plan = order.plan_type.value

        logger.info(f"Generating love analysis for {p1_name} & {p2_name} (Plan: {plan})")

        if self.is_mock_enabled():
            logger.warning("Anthropic API is in MOCK mode. Returning realistic mock response.")
            return self._generate_mock_analysis(p1_name, p1_birth, p2_name, p2_birth, plan)

        # Craft highly premium prompt based on the selected plan
        prompt = self._craft_compatibility_prompt(p1_name, p1_birth, p2_name, p2_birth, plan)

        try:
            # Call Claude 3.5 Sonnet / Haiku for highly elaborate analysis
            model_name = "claude-3-5-sonnet-20240620" if plan == "PREMIUM" else "claude-3-haiku-20240307"
            
            message = self.client.messages.create(
                model=model_name,
                max_tokens=4000 if plan == "PREMIUM" else 2000,
                temperature=0.7,
                system=(
                    "Tu es un expert mondial en relations de couple, psychologie relationnelle, sexologie et astrologie humaniste. "
                    "Ton ton est bienveillant, profond, mystique mais ancré dans une psychologie moderne. Tu t'exprimes en français "
                    "de manière extrêmement raffinée. Tu génères des analyses détaillées, sans raccourcis de texte, qui seront "
                    "compilées en rapports PDF haut de gamme."
                ),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            # Fallback to premium mockup instead of throwing error, protecting B2C billing
            return self._generate_mock_analysis(p1_name, p1_birth, p2_name, p2_birth, plan)

    def _craft_compatibility_prompt(self, p1: str, b1: str, p2: str, b2: str, plan: str) -> str:
        base_instructions = f"""
Génère une analyse approfondie de compatibilité amoureuse pour le couple suivant :
Partenaire 1 : {p1} (né(e) le {b1})
Partenaire 2 : {p2} (né(e) le {b2})

Rédige l'analyse EN FRANÇAIS sous forme de rapport structuré en Markdown.
Utilise des titres hiérarchisés (##, ###) et un ton captivant, émotionnel et professionnel.
Ne fais aucune introduction administrative ou méta-commentaire, commence directement par l'analyse amoureuse.
"""
        
        if plan == "PREMIUM":
            return base_instructions + f"""
Ce couple a souscrit à notre formule **PREMIUM**. Le rapport doit être extrêmement complet, riche et structuré pour s'étendre sur 8 à 12 pages après conversion PDF.

Tu dois impérativement aborder en détail les 8 chapitres suivants, avec au moins 3 paragraphes denses par chapitre :

1. **Introduction et Énergie Initiale du Couple** (Analyse vibratoire de l'alliance entre {p1} et {p2})
2. **Le Pilier Émotionnel** (Comment leurs cœurs se connectent, leurs sensibilités mutuelles, empathie et blessures d'attachement respectives)
3. **Le Pilier de la Communication** (Comment ils échangent, résolvent les conflits, les malentendus typiques et les clés pour s'entendre)
4. **Alchimie, Passion et Intimité** (Le magnétisme physique, l'alchimie sensuelle, l'expression du désir et leur connexion intime)
5. **Défis Caractéristiques de cette Union** (Les points de friction potentiels, ce qui pourrait les séparer ou causer de l'usure)
6. **Harmonie de Vie et Projets Communs** (Leur vision à long terme : foyer, finances, famille, voyages et ambitions de vie)
7. **Bilan Numérologique et Astrologique Synastrique** (Utilise leurs dates de naissance : {b1} et {b2} pour calculer et expliquer leurs chemins de vie et planètes de compatibilité de façon symbolique et inspirante)
8. **Plan d'Action du Couple (Les 10 Commandements)** (10 conseils ultra-personnalisés et actionnables pour surmonter leurs défis et faire durer leur amour toute une vie)

Renseigne des métaphores poétiques et des analyses psychologiques profondes. Sois très généreux sur le texte.
"""
        else:
            return base_instructions + f"""
Ce couple a souscrit à notre formule **ESSENTIEL**. Rédige un rapport équilibré et percutant de 4 chapitres :

1. **La Connexion Initiale** (Vibe globale entre {p1} et {p2})
2. **Communication & Émotions** (Le dialogue du cœur et de l'esprit)
3. **Alchimie & Magnétisme** (Leur dynamique d'attraction intime)
4. **Conseils d'Or pour l'Avenir** (3 conseils concrets pour consolider leur amour)
"""

    def _generate_mock_analysis(self, p1: str, b1: str, p2: str, b2: str, plan: str) -> str:
        """
        Generates structured romantic compatibility reports in French.
        Used for local offline development, tests, or API fallback.
        """
        if plan == "PREMIUM":
            return f"""# Rapport de Compatibilité Spirituelle & Emotionnelle
## {p1} & {p2}

---

## Chapitre 1 : Introduction et Énergie Initiale du Couple

L'union de {p1} et {p2} s'annonce sous des auspices vibratoires fascinants. En analysant la résonance de leurs prénoms et la géométrie sacrée de leurs chemins de vie issus de leurs dates de naissance ({b1} et {b2}), on perçoit immédiatement une polarité dynamique. Il ne s'agit pas d'une simple rencontre fortuite, mais d'une attraction magnétique qui bouscule les structures établies. 

{p1} apporte à cette relation une structure solide, une quête d'harmonie concrète et une sensibilité à fleur de peau, souvent dissimulée derrière une façade de maîtrise. {p2}, de son côté, rayonne d'une énergie d'exploration, de renouveau et d'une intensité spirituelle qui agit comme un catalyseur sur son partenaire. Ensemble, vous créez une bulle intime où la réalité quotidienne prend des couleurs poétiques.

La première rencontre vibratoire indique un accord majeur : une capacité à rêver ensemble. Cependant, la tension nécessaire à toute évolution est présente. Ce couple possède l'étincelle des grandes histoires, celles qui forcent chacun à grandir, à guérir ses vieilles blessures d'enfance, et à réapprendre le langage de la confiance absolue.

---

## Chapitre 2 : Le Pilier Émotionnel et la Fusion des Cœurs

Sur le plan émotionnel, la compatibilité entre {p1} et {p2} touche à une profondeur rare. Vous n'êtes pas de ceux qui se contentent de conversations superficielles. La connexion s'établit au niveau du non-dit, des regards partagés et des silences habités. 

* **La vulnérabilité de {p1}** : Face à la présence de {p2}, {p1} ressent à la fois le désir de s'ouvrir totalement et la peur instinctive d'être mis(e) à nu. Cette ambivalence est normale et fait partie de votre processus d'apprentissage.
* **L'empathie de {p2}** : {p2} possède l'antenne intuitive nécessaire pour capter les micro-variations d'humeur de {p1}, offrant un espace de sécurité émotionnelle unique, bien que parfois submergé par sa propre émotivité.

Votre défi majeur dans ce chapitre réside dans la gestion de vos éponges émotionnelles réciproques. Parce que vous ressentez tout au décuple, un nuage passager chez l'un peut provoquer une tempête existentielle chez l'autre. Apprendre à différencier vos propres émotions de celles de votre partenaire sera la clé de voûte de votre stabilité affective.

---

## Chapitre 3 : Le Pilier de la Communication et la Résolution des Tempêtes

Comment dialoguent les âmes de {p1} et {p2} ? Votre style de communication est hautement instinctif. Vous partagez une forme de télépathie amoureuse qui fait souvent l'admiration de votre entourage. Vous finissez les phrases de l'autre et devinez ses intentions bien avant qu'elles ne soient formulées.

Néanmoins, en cas de désaccord, les schémas de défense s'activent de façon marquée. {p1} aura tendance à se replier dans son silence protecteur, analysant les faits avec une apparente froideur pour éviter d'être blessé(e). À l'inverse, {p2} aura besoin d'une résolution immédiate, parfois verbale et passionnée, interprétant le retrait de son partenaire comme un abandon ou un désintérêt.

Pour harmoniser ce pilier :
1. **Instaurez la règle du sas** : Permettez à {p1} de prendre un temps de réflexion avant de parler, sans que {p2} ne se sente exclu(e).
2. **Pratiquez l'écoute active** : Reformulez les besoins de l'autre sans chercher à avoir raison à tout prix.

---

## Chapitre 4 : Alchimie, Passion et Intimité Sacrée

Sur le plan de l'intimité, le feu créateur brûle avec une intensité rare. L'alchimie entre {p1} et {p2} dépasse largement le cadre purement physique pour s'élever au rang d'une véritable union tantrique. C'est dans le secret de votre espace sacré que vos différences se résolvent et fusionnent.

Il y a une dimension magnétique indéniable : {p1} est fasciné(e) par la sensualité et le mystère magnétique de {p2}, tandis que {p2} trouve dans les bras de {p1} un ancrage rassurant et une intensité qui le(la) stabilise. Les moments d'intimité agissent pour votre couple comme un véritable bain de régénération énergétique.

Votre sexualité n'est pas routinière; elle se nourrit de complicité, de jeux, de délicatesse et d'une curiosité mutuelle. Veillez à préserver cet espace des intrusions du stress quotidien, car c'est le baromètre le plus fiable de la santé globale de votre couple.

---

## Chapitre 5 : Défis Majeurs et Points de Friction

Aucune grande alliance ne vient sans défis de taille. Pour {p1} et {p2}, l'obstacle principal est le piège de la fusion excessive. À force de vouloir ne faire qu'un, vous risquez de perdre vos individualités et d'étouffer la passion, qui a besoin d'air et de distance pour se renouveler.

Un autre point de friction réside dans la gestion du contrôle. {p1} aime planifier, structurer l'avenir et sécuriser le foyer, ce qui peut parfois être perçu par {p2} comme une restriction de sa liberté et de sa spontanéité créative. Trouver le juste équilibre entre structure et liberté sera votre grand œuvre.

---

## Chapitre 6 : Harmonie de Vie et Projets Communs

Construire un empire à deux est tout à fait dans vos cordes. Vos visions du monde, bien que colorées différemment, convergent vers le même désir profond : créer un foyer chaleureux, esthétique, et propice à l'accueil de vos proches. Vous formez une excellente équipe pour matérialiser vos rêves.

* **Le rôle de bâtisseur** : {p1} excelle à structurer les étapes des projets (achat immobilier, gestion financière, logistique).
* **Le rôle d'inspirateur** : {p2} insuffle l'âme, le design, la créativité et les relations publiques de vos projets communs.

---

## Chapitre 7 : Bilan Astrologique & Numérologique Synastrique

En mariant les énergies vibratoires du **{b1}** et du **{b2}**, nous obtenons une synastrie d'une rare élégance. Le couple exprime une forte présence de l'élément Eau (l'intuition, les sentiments) complétée par une structure de Terre qui garantit la pérennité.

Vos nombres de destin personnels révèlent un chemin de vie complémentaire qui vous pousse mutuellement à sortir de vos zones de confort respectives. Votre alliance est karmique : elle vise à guérir des mémoires familiales anciennes pour vous permettre de vivre un amour pleinement conscient et libéré du passé.

---

## Chapitre 8 : Le Plan d'Action du Couple (Les 10 Commandements)

Pour faire de votre amour une œuvre intemporelle, voici vos dix règles d'or personnalisées :

1. **Honorez vos jardins secrets** : Gardez des activités et des passions individuelles pour nourrir le désir.
2. **Célébrez les rituels du soir** : Prenez 10 minutes chaque jour pour vous reconnecter sans écrans.
3. **Désamorcez par le rire** : Utilisez votre complicité humoristique pour faire tomber les tensions.
4. **Acceptez l'imperfection de l'autre** : Aimez les failles de votre partenaire, c'est là que passe la lumière.
5. **Valorisez les efforts du bâtisseur** : {p2} doit exprimer sa gratitude pour le travail de structure de {p1}.
6. **Nourrissez la spontanéité** : {p1} doit accepter de partir à l'aventure sans planifier de temps en temps.
7. **Parlez le langage de l'autre** : Découvrez et pratiquez les langages de l'amour dominants chez votre partenaire.
8. **Créez un sanctuaire** : Faites de votre chambre à coucher un espace exclusivement dédié à l'amour et au repos.
9. **Exprimez vos peurs d'abandon** : Verbalisez vos doutes plutôt que de vous murer dans le silence ou la colère.
10. **Croyez en votre force** : Rappelez-vous, dans les moments de doute, la beauté unique de l'étincelle qui vous a unis.
"""
        else:
            return f"""# Analyse de Compatibilité
## {p1} & {p2}

---

## Chapitre 1 : La Connexion Initiale
L'union de {p1} et {p2} est guidée par une belle harmonie naturelle. Vos énergies se complètent harmonieusement : {p1} apporte un ancrage rassurant et une clarté d'esprit, tandis que {p2} insuffle un vent de créativité, de sensibilité et de renouveau dans votre quotidien. Ensemble, vous formez un couple équilibré et résilient.

## Chapitre 2 : Communication & Émotions
Votre communication est fluide et intuitive. Vous parvenez facilement à comprendre les états d'âme de l'autre sans longs discours. Votre sensibilité mutuelle vous permet de créer une atmosphère sécurisante et chaleureuse. Veillez simplement, lors des désaccords, à ce que {p1} ne se renferme pas dans le silence et à ce que {p2} exprime ses besoins avec calme.

## Chapitre 3 : Alchimie & Magnétisme
Physiquement et spirituellement, l'attraction entre vous est forte. Il y a un profond respect mutuel doublé d'une alchimie sensuelle vibrante. Votre intimité est un espace de confiance et de complicité ludique où vous aimez vous ressourcer et explorer de nouvelles dimensions à deux.

## Chapitre 4 : Conseils d'Or pour l'Avenir
Pour pérenniser votre amour :
1. **Communiquez avec bienveillance** : Ne laissez aucun non-dit s'accumuler.
2. **Préservez vos espaces personnels** : L'indépendance de chacun enrichit la relation.
3. **Cultivez la surprise** : Cassez la routine quotidienne par des rendez-vous improvisés.
"""

claude_service = ClaudeService()
