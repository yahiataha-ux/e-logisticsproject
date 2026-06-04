import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PDF_PATH = r"c:\Users\hp\Documents\ENSAM\S8\ZZ PROJET METIERS\Get Rich or Die Tryin\screenshots\cahier_des_charges.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        # Draw header (except on first page)
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0f172a"))
            self.drawString(54, 800, "ATLAS LOGISTICS - CAHIER DES CHARGES")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(A4[0]-54, 800, "Système ERP & Supply Chain Responsable")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 792, A4[0]-54, 792)
            
            # Draw footer
            self.line(54, 50, A4[0]-54, 50)
            self.drawString(54, 38, "© 2026 Atlas Logistics Morocco. Opérations Neutres en Carbone.")
            self.drawRightString(A4[0]-54, 38, f"Page {self._pageNumber} sur {page_count}")
            self.restoreState()
        else:
            # First page cover styling
            self.saveState()
            # Draw green background accent block on the left
            self.setFillColor(colors.HexColor("#064e3b"))
            self.rect(0, 0, 30, A4[1], fill=1, stroke=0)
            self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor("#064e3b"),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#334155"),
        spaceAfter=40
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=5
    )
    
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=6
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=10
    )

    story = []
    
    # --- PAGE 1: COVER PAGE ---
    story.append(Spacer(1, 150))
    story.append(Paragraph("Atlas Logistics", title_style))
    story.append(Paragraph("Cahier des Charges Fonctionnel & Technique", subtitle_style))
    story.append(Spacer(1, 100))
    
    story.append(Paragraph("<b>Projet</b> : Système d'optimisation Supply Chain éco-responsable", meta_style))
    story.append(Paragraph("<b>Date de publication</b> : Juin 2026", meta_style))
    story.append(Paragraph("<b>Version</b> : 1.0.0", meta_style))
    story.append(Paragraph("<b>Auteur</b> : Antigravity AI & ENSAM Métiers", meta_style))
    story.append(PageBreak())
    
    # --- PAGE 2: TABLE OF CONTENTS & INTRODUCTION ---
    story.append(Paragraph("1. Contexte et Objectifs du Projet", h1_style))
    story.append(Paragraph("<b>Contexte</b><br/>La logistique moderne fait face à deux défis majeurs : l'efficacité opérationnelle (délais de livraison, gestion d'inventaire) et la responsabilité environnementale (émissions de gaz à effet de serre). Au Maroc, les PME locales font face à des coûts de distribution élevés et manquent d'outils ERP pour optimiser leur stockage et leurs tournées de livraison.", body_style))
    
    story.append(Paragraph("<b>Objectifs d'Atlas Logistics</b>", h2_style))
    story.append(Paragraph("• <b>Éco-responsabilité</b> : Placer la réduction du CO2 au cœur de la prise de décision en mesurant et affichant l'impact carbone de chaque trajet.", bullet_style))
    story.append(Paragraph("• <b>Optimisation des Flux</b> : Utiliser des algorithmes de recherche de chemin (Dijkstra) et d'ordonnancement de tournées (Plus proche voisin) pour raccourcir les trajets de livraison.", bullet_style))
    story.append(Paragraph("• <b>Gestion Avancée d'Inventaire</b> : Modéliser des hubs de stockage physiques par ville avec des grilles de placement 2D dynamiques (Rails et Étagères) et des politiques de stock adaptables.", bullet_style))
    story.append(Paragraph("• <b>Synergie Locale</b> : Connecter 4 acteurs clés (les Administrateurs Atlas, les Entreprises/Fournisseurs PME, les Chauffeurs/Livreurs et les Clients finaux).", bullet_style))
    
    # --- SECTION 2: ROLES ---
    story.append(Paragraph("2. Rôles et Parcours Utilisateurs", h1_style))
    story.append(Paragraph("L'application repose sur 4 rôles majeurs disposant chacun d'un tableau de bord personnalisé :", body_style))
    
    story.append(Paragraph("<b>2.1. Espace Administrateur (Global Control Tower)</b>", h2_style))
    story.append(Paragraph("L'administrateur supervise la totalité de l'infrastructure logistique :", body_style))
    story.append(Paragraph("• <b>Tableau de Bord Premium</b> : Visualisation des KPIs globaux (Chiffre d'affaires total, tonnes de CO2 économisées, taux de livraison active).", bullet_style))
    story.append(Paragraph("• <b>Impersonnalisation ('Login as')</b> : Capacité à se connecter à la place de n'importe quel autre utilisateur en un clic pour assistance rapide ou démo.", bullet_style))
    story.append(Paragraph("• <b>Gestion des Hubs & Inventaires</b> : Ajout de nouveaux entrepôts dans les villes marocaines majeures et surveillance de leur taux de saturation.", bullet_style))
    story.append(Paragraph("• <b>Visualisation 2D d'entrepôt</b> : Grille modélisant l'occupation physique des rails et étagères pour chaque hub.", bullet_style))
    story.append(Paragraph("• <b>Monitoring Cartographique</b> : Carte interactive (Leaflet JS) montrant en temps réel la position GPS des chauffeurs en tournée et les routes optimales calculées.", bullet_style))
    story.append(Paragraph("• <b>Analytics</b> : Graphiques Chart.js consolidant l'impact CO2 par ville.", bullet_style))

    story.append(Paragraph("<b>2.2. Espace Entreprise (SMEs & Fournisseurs)</b>", h2_style))
    story.append(Paragraph("Les entreprises partenaires déposent leurs marchandises dans les hubs Atlas et gèrent leurs ventes :", body_style))
    story.append(Paragraph("• <b>Publication de Produits</b> : Ajout de produits au catalogue avec affectation directe à un hub d'origine.", bullet_style))
    story.append(Paragraph("• <b>Gestion des Stocks</b> : Réapprovisionnement des stocks et déploiement rapide d'un produit existant sur d'autres hubs régionaux.", bullet_style))
    story.append(Paragraph("• <b>Traitement des Commandes</b> : Suivi des ventes et affectation des transporteurs.", bullet_style))
    story.append(Paragraph("• <b>Exports documentaires</b> : Excel (.xlsx) pour les ventes, PDF pour les Bons de Sortie d'entrepôt, et Certificat Vert de Durabilité (PDF) attestant du CO2 économisé.", bullet_style))

    story.append(PageBreak())

    story.append(Paragraph("<b>2.3. Espace Chauffeur (Logistique Terrain)</b>", h2_style))
    story.append(Paragraph("Les conducteurs exécutent les tournées calculées :", body_style))
    story.append(Paragraph("• <b>Gestion des Tournées</b> : Carte locale montrant les arrêts de livraison classés dans l'ordre le plus efficace.", bullet_style))
    story.append(Paragraph("• <b>Mise à Jour de Statuts</b> : Possibilité de passer en mode Disponible, En livraison, En pause ou Hors service.", bullet_style))
    story.append(Paragraph("• <b>Validation Terrain</b> : Boutons rapides pour marquer une mission comme 'Livrée' (ce qui crédite l'impact carbone économisé sur son profil) ou 'Échec' avec motif.", bullet_style))
    story.append(Paragraph("• <b>Bilan Personnel</b> : Historique des missions et équivalence du CO2 économisé en nombre d'arbres plantés.", bullet_style))

    story.append(Paragraph("<b>2.4. Espace Client (Marketplace Éco-citoyenne)</b>", h2_style))
    story.append(Paragraph("Le client final achète des produits locaux et suit sa commande :", body_style))
    story.append(Paragraph("• <b>Marketplace Éco-indexée</b> : Classement des produits selon un Performance Index qui combine le prix et l'impact CO2 théorique (distance par rapport au hub le plus proche). Un code couleur (Vert, Orange, Rouge) sensibilise l'acheteur.", bullet_style))
    story.append(Paragraph("• <b>Bilan d'Impact Personnel</b> : Graphique et bilan de son impact écologique cumulé suite à ses achats.", bullet_style))
    story.append(Paragraph("• <b>Suivi de Commande interactif</b> : Carte montrant le trajet prévu entre le hub d'origine et la livraison finale, avec l'emplacement actuel estimé du chauffeur.", bullet_style))

    # --- SECTION 3: ARCHITECTURE ---
    story.append(Paragraph("3. Architecture Technique", h1_style))
    story.append(Paragraph("• <b>Framework Principal</b> : Django (Python) pour une structure robuste, sécurisée et modulaire.", bullet_style))
    story.append(Paragraph("• <b>Base de Données</b> : SQLite (en développement) - extensible vers PostgreSQL pour la production.", bullet_style))
    story.append(Paragraph("• <b>Styling UI</b> : Tailwind CSS assurant une interface fluide et un design éco-futuriste (palette verte émeraude, gris ardoise, effets de transparence/glassmorphism).", bullet_style))
    story.append(Paragraph("• <b>Cartographie & Graphs</b> : Leaflet JS pour le rendu dynamique des cartes OpenStreetMap et le tracé des itinéraires, et Chart.js pour les graphiques de suivi CO2.", bullet_style))
    story.append(Paragraph("• <b>Générateurs documentaires</b> : ReportLab (génération de PDFs dynamiques à la volée) et Pandas / openpyxl (génération d'exports Excel structurés).", bullet_style))

    # --- SECTION 4: ALGORITHMS ---
    story.append(Paragraph("4. Algorithmes au Cœur du Système", h1_style))
    
    story.append(Paragraph("<b>4.1. Algorithme de Dijkstra (Optimisation du chemin)</b>", h2_style))
    story.append(Paragraph("Utilisé lors de l'assignation d'une commande pour calculer l'itinéraire le plus efficace à travers le graphe routier des villes marocaines (Casablanca, Rabat, Tanger, Marrakech, etc.). L'itinéraire optimisé (Dijkstra) est comparé à un trajet 'non optimisé' classique (estimé à +35% de distance en raison d'un mauvais aiguillage) afin de quantifier exactement l'économie de carbone (en kg CO2).", body_style))
    
    story.append(Paragraph("<b>4.2. Algorithme du Plus Proche Voisin (Greedy Nearest Neighbor)</b>", h2_style))
    story.append(Paragraph("Utilisé sur le terminal chauffeur pour trier sa liste d'arrêts de livraison quotidienne en recherchant à chaque étape l'arrêt restant le plus proche géographiquement.", body_style))
    
    story.append(Paragraph("<b>4.3. Politiques d'allocation de stock (Warehouse Management)</b>", h2_style))
    story.append(Paragraph("L'administrateur peut réordonner globalement les produits dans les hubs en appliquant des stratégies : DEMAND (Proximité Demande - les produits les plus vendus sont mis près des rails de sortie), FIFO, LIFO, SPT, ou LPT.", body_style))

    # --- SECTION 5: DATA MODEL ---
    story.append(PageBreak())
    story.append(Paragraph("5. Modélisation des Données (Base de Données)", h1_style))
    story.append(Paragraph("Le modèle de données d'Atlas Logistics est conçu pour s'adapter à la fois aux contraintes ERP d'inventaire et aux contraintes cartographiques GPS :", body_style))
    
    story.append(Paragraph("• <b>Table Utilisateur (authentication.User)</b> : Hérite de la table AbstractUser en y ajoutant : <i>role</i> (Admin, Entreprise, Transporteur, Client), <i>company_name</i>, <i>last_activity</i>, <i>stock_strategy</i> et les notes de performance (<i>rating_co2, rating_time, rating_price</i>).", bullet_style))
    story.append(Paragraph("• <b>Table Entrepôt / Hub (logistics_core.Warehouse)</b> : Représente un hub de stockage physique : <i>name</i>, <i>city</i>, <i>capacity</i>, <i>total_rails, total_shelves</i> et coordonnées géographiques (<i>lat, lng</i>).", bullet_style))
    story.append(Paragraph("• <b>Table Produit (logistics_core.Product)</b> : Représente les articles physiques stockés : <i>name, price, stock, category, image</i>, liaisons vers le vendeur et l'entrepôt, coordonnées de placement (<i>rail, shelf</i>) et <i>co2_impact</i>.", bullet_style))
    story.append(Paragraph("• <b>Table Commande (client.Order)</b> : Enregistre les transactions : liaison client, liaison produit, <i>quantity</i>, <i>price_total</i>, <i>status</i>, <i>co2_emission</i> réelle de livraison, et <i>order_date</i>.", bullet_style))
    story.append(Paragraph("• <b>Table Mission de Livraison (transporter.MissionLivraison)</b> : Lie une commande à un chauffeur physique et un entrepôt de départ. Enregistre l'état de livraison (<i>statut</i>), la <i>distance_km</i> réelle et le bilan carbone comparatif (<i>co2_estime_kg</i>, <i>co2_mode_classique_kg</i>, <i>co2_economise_kg</i>).", bullet_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF successfully generated.")

if __name__ == "__main__":
    build_pdf()
