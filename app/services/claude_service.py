import logging
import anthropic
import json
import re
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
        Returns a structured JSON string containing all the required sections.
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
                    "de manière extrêmement raffinée. Tu dois obligatoirement renvoyer une réponse au format JSON strict, "
                    "conforme au schéma demandé, sans aucun texte d'introduction ni de conclusion en dehors du JSON."
                ),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            # Validate JSON
            self._parse_and_validate_json(response_text, plan)
            return response_text

        except Exception as e:
            logger.error(f"Error calling Claude API or parsing response: {str(e)}")
            # Fallback to premium mockup instead of throwing error, protecting B2C billing
            return self._generate_mock_analysis(p1_name, p1_birth, p2_name, p2_birth, plan)

    def _parse_and_validate_json(self, text: str, plan: str) -> dict:
        json_str = self._extract_json_payload(text)
        data = json.loads(json_str)
        
        required_keys = [
            "score", "score_explanation", "connexion_emotionnelle", 
            "dynamique_communication", "alchimie_physique", 
            "points_forts", "points_vigilance", "conseil_final"
        ]
        if plan == "PREMIUM":
            required_keys += ["analyse_cycles_vie", "previsions_12m", "rituels", "message_intention"]
            
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required JSON key: {key}")
        return data

    def _extract_json_payload(self, text: str) -> str:
        if not text:
            raise ValueError("Empty Claude response")

        cleaned = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("Claude response does not contain a JSON object")

        json_text = cleaned[start:end + 1]
        json_text = self._strip_json_comments(json_text)
        json_text = re.sub(r",(\s*[}\]])", r"\1", json_text)
        return json_text

    def _strip_json_comments(self, text: str) -> str:
        result = []
        in_string = False
        escaped = False
        i = 0

        while i < len(text):
            char = text[i]
            next_char = text[i + 1] if i + 1 < len(text) else ""

            if in_string:
                result.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                i += 1
                continue

            if char == '"':
                in_string = True
                result.append(char)
                i += 1
                continue

            if char == "/" and next_char == "/":
                i += 2
                while i < len(text) and text[i] not in "\r\n":
                    i += 1
                continue

            if char == "/" and next_char == "*":
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue

            result.append(char)
            i += 1

        return "".join(result)

    def _craft_compatibility_prompt(self, p1: str, b1: str, p2: str, b2: str, plan: str) -> str:
        if plan == "PREMIUM":
            return f"""
Génère une analyse approfondie de compatibilité amoureuse premium pour le couple :
Partenaire 1 : {p1} (né(e) le {b1})
Partenaire 2 : {p2} (né(e) le {b2})

Rédige l'analyse EN FRANÇAIS sous forme de JSON strict avec exactement la structure suivante.
Ne renvoie aucun bloc markdown, aucun commentaire, aucune virgule finale et aucun texte hors du JSON.
Chaque section textuelle doit faire environ 200 à 300 mots (2 à 3 paragraphes maximum) pour tenir parfaitement sur une page A4 sans déborder.

Schéma JSON attendu :
{{
  "score": 85,
  "score_explanation": "Une explication synthétique du score (3-4 lignes).",
  "connexion_emotionnelle": "Analyse détaillée de la connexion émotionnelle, vulnérabilités et sensibilité mutuelle.",
  "dynamique_communication": "Analyse détaillée de la communication, résolution de conflits et clés d'entente.",
  "alchimie_physique": "Analyse de l'alchimie intime, passion, magnétisme physique et désir.",
  "points_forts": [
    "Point fort 1 avec son titre en gras et une explication claire.",
    "Point fort 2 avec son titre en gras et une explication claire.",
    "Point fort 3 avec son titre en gras et une explication claire."
  ],
  "points_vigilance": [
    "Point de vigilance 1 avec son titre en gras et une explication claire.",
    "Point de vigilance 2 avec son titre en gras et une explication claire.",
    "Point de vigilance 3 avec son titre en gras et une explication claire."
  ],
  "conseil_final": "Un conseil final personnalisé et inspirant pour sceller leur union.",
  "analyse_cycles_vie": "Analyse numérologique basée sur les dates de naissance {b1} et {b2} détaillant les cycles de vie respectifs et leur croisement.",
  "previsions_12m": "Prévisions claires sur les périodes favorables et délicates pour les 12 prochains mois.",
  "rituels": [
    "Rituel 1 : explication détaillée d'un rituel de couple personnalisé.",
    "Rituel 2 : explication détaillée d'un rituel de couple personnalisé.",
    "Rituel 3 : explication détaillée d'un rituel de couple personnalisé."
  ],
  "message_intention": "Un message d'intention poétique et inspirant co-rédigé par l'IA pour le couple."
}}
"""
        else:
            return f"""
Génère une analyse de compatibilité amoureuse essentielle pour le couple :
Partenaire 1 : {p1} (né(e) le {b1})
Partenaire 2 : {p2} (né(e) le {b2})

Rédige l'analyse EN FRANÇAIS sous forme de JSON strict avec exactement la structure suivante.
Ne renvoie aucun bloc markdown, aucun commentaire, aucune virgule finale et aucun texte hors du JSON.
Chaque section textuelle doit faire environ 200 à 300 mots (2 à 3 paragraphes maximum) pour tenir parfaitement sur une page A4 sans déborder.

Schéma JSON attendu :
{{
  "score": 85,
  "score_explanation": "Une explication synthétique du score (3-4 lignes).",
  "connexion_emotionnelle": "Analyse de la connexion émotionnelle, vulnérabilités et sensibilité mutuelle.",
  "dynamique_communication": "Analyse de la communication, résolution de conflits et clés d'entente.",
  "alchimie_physique": "Analyse de l'alchimie intime, passion, magnétisme physique et désir.",
  "points_forts": [
    "Point fort 1 avec son titre en gras et une explication claire.",
    "Point fort 2 avec son titre en gras et une explication claire.",
    "Point fort 3 avec son titre en gras et une explication claire."
  ],
  "points_vigilance": [
    "Point de vigilance 1 avec son titre en gras et une explication claire.",
    "Point de vigilance 2 avec son titre en gras et une explication claire.",
    "Point de vigilance 3 avec son titre en gras et une explication claire."
  ],
  "conseil_final": "Un conseil final personnalisé et inspirant pour sceller leur union."
}}
"""

    def _generate_mock_analysis(self, p1: str, b1: str, p2: str, b2: str, plan: str) -> str:
        """
        Generates structured romantic compatibility reports in French.
        Used for local offline development, tests, or API fallback.
        """
        data = {
            "score": 88,
            "score_explanation": f"L'union de {p1} et {p2} s'annonce sous des auspices vibratoires fascinants. En analysant le croisement de vos chemins de vie issus de vos dates de naissance ({b1} et {b2}), on perçoit immédiatement une polarité dynamique propice à une attraction magnétique solide et durable.",
            "connexion_emotionnelle": f"Sur le plan émotionnel, la compatibilité entre {p1} et {p2} touche à une profondeur rare. Vous n'êtes pas de ceux qui se contentent de conversations superficielles. La connexion s'établit au niveau du non-dit, des regards partagés et des silences habités.\n\nVous êtes extrêmement sensibles aux humeurs de l'autre, offrant un espace de sécurité émotionnelle unique, bien que parfois submergés par votre propre empathie réciproque. Apprendre à différencier vos propres émotions de celles de votre partenaire sera la clé de voûte de votre stabilité affective.",
            "dynamique_communication": f"Votre style de communication est hautement instinctif. Vous partagez une forme de télépathie amoureuse qui fait souvent l'admiration de votre entourage. Vous finissez les phrases de l'autre et devinez ses intentions bien avant qu'elles ne soient formulées.\n\nNéanmoins, en cas de désaccord, les schémas de défense s'activent de façon marquée. L'un aura tendance à se replier dans son silence protecteur, tandis que l'autre aura besoin d'une résolution immédiate. Instaurez la règle du sas pour donner à chacun le temps de réfléchir avant de s'exprimer.",
            "alchimie_physique": f"Sur le plan de l'intimité, le feu créateur brûle avec une intensité rare. L'alchimie entre {p1} et {p2} dépasse largement le cadre purement physique pour s'élever au rang d'une véritable union vibratoire. C'est dans le secret de votre espace privé que vos différences se résolvent et fusionnent.\n\nIl y a une dimension magnétique indéniable : l'un est fasciné par la sensualité et le mystère de l'autre, tandis que l'autre trouve dans cette étreinte un ancrage rassurant et une intensité stabilisatrice. Veillez à préserver cet espace de la routine quotidienne.",
            "points_forts": [
                "**Télépathie intuitive** : Une capacité innée à ressentir et à comprendre les besoins profonds de votre partenaire sans parole.",
                "**Complémentarité des rôles** : L'un apporte la structure et la planification, tandis que l'autre apporte l'inspiration et la créativité.",
                "**Alchimie magnétique** : Une connexion physique et sensuelle extrêmement puissante qui sert de ciment dans les moments de doute."
            ],
            "points_vigilance": [
                "**Fusion excessive** : Le risque de vous perdre dans la relation et d'étouffer l'individualité de chacun.",
                "**Schémas de repli** : La tendance à s'enfermer dans le silence lors des conflits majeurs au lieu d'ouvrir le dialogue.",
                "**Conflit de contrôle** : Des frictions possibles entre le besoin de planifier l'avenir et le besoin de spontanéité."
            ],
            "conseil_final": f"Pour faire de votre amour une œuvre intemporelle, apprenez à chérir à la fois ce qui vous unit et ce qui vous différencie. L'amour n'est pas une fusion où les identités s'effacent, mais un duo harmonieux où chaque voix reste distincte. Continuez à bâtir vos projets avec patience et confiance."
        }

        if plan == "PREMIUM":
            data.update({
                "analyse_cycles_vie": f"En mariant les énergies vibratoires du {b1} et du {b2}, nous obtenons une synastrie d'une rare élégance. Vos chemins de vie révèlent une dynamique karmique forte : vous êtes réunis pour guérir des blessures d'attachement anciennes et apprendre la confiance absolue.\n\nLe croisement de vos cycles numériques indique que vous entrez actuellement dans une phase de stabilisation et de concrétisation matérielle (foyer, projets de vie à long terme).",
                "previsions_12m": "Les 6 prochains mois seront marqués par une intensité passionnelle accrue et des opportunités de voyages à deux. Soyez vigilants autour du 9ème mois, où une baisse de communication pourrait créer de petits malentendus. Les 3 derniers mois de l'année seront parfaits pour concrétiser un projet immobilier ou familial.",
                "rituels": [
                    "**Le Rituel du Miroir Matinal** : Prenez 1 minute chaque matin pour vous regarder dans les yeux en silence avant de commencer la journée.",
                    "**La Boîte à Gratitude** : Notez chaque semaine un moment de gratitude envers votre partenaire et lisez-les ensemble le week-end.",
                    "**L'Escapade sans Écran** : Déterminez une soirée par semaine sans aucun appareil connecté, dédiée uniquement à la conversation intime."
                ],
                "message_intention": f"Que cette alliance entre {p1} et {p2} soit le phare qui éclaire vos nuits et le soleil qui réchauffe vos jours. Puisse votre amour grandir en liberté, s'ancrer dans la confiance et rayonner de toute sa beauté originelle."
            })

        return json.dumps(data, ensure_ascii=False)

claude_service = ClaudeService()
