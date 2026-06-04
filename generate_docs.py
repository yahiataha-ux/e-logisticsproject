from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
import os

def generate_static_methodology():
    file_path = "Methodologie_Calcul_CO2_Atlas.pdf"
    p = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFillColor(colors.HexColor("#064e3b"))
    p.rect(0, height-4*cm, width, 4*cm, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(2*cm, height-2*cm, "Guide de Calcul CO2 & Certification")
    p.setFont("Helvetica", 10)
    p.drawString(2*cm, height-3*cm, "Documentation technique - Plateforme Atlas Logistics")
    
    # Section 1
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    y = height - 6*cm
    p.drawString(2*cm, y, "1. Méthode de calcul de l'économie carbone")
    p.setFont("Helvetica", 11)
    y -= 0.8*cm
    text = [
        "L'économie de CO2 est calculée en comparant l'empreinte de base d'un produit avec",
        "sa réduction obtenue grâce à l'optimisation logistique d'Atlas.",
        "",
        "Formule : CO2_Economisé = (CO2_Base * Score_Ordonnancement) + (Volume * Bonus_Hubs)",
        "",
        "- Score_Ordonnancement : La stratégie 'Demande Client' réduit l'impact de 28% car elle",
        "  minimise les trajets de picking en plaçant les produits à forte rotation près de la sortie.",
        "- Bonus_Hubs : Chaque entrepôt régional utilisé réduit de 4% les émissions liées au transport,",
        "  en rapprochant physiquement le stock du client final."
    ]
    for line in text:
        p.drawString(2*cm, y, line)
        y -= 0.6*cm
        
    # Section 2
    y -= 1*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, "2. Critères de Certification")
    p.setFont("Helvetica", 11)
    y -= 0.8*cm
    criteria = [
        "Pour être certifié Atlas Green, un entrepôt doit valider les points suivants :",
        "1. Saturation des véhicules > 85% (Pas de trajets à vide).",
        "2. Utilisation du planogramme IA pour l'organisation des rails.",
        "3. Présence dans au moins 3 hubs stratégiques pour limiter les distances.",
        "4. Réduction prouvée de plus de 15% du CO2 par rapport à un flux standard."
    ]
    for line in criteria:
        p.drawString(2*cm, y, line)
        y -= 0.6*cm

    # Section 3
    y -= 1*cm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2*cm, y, "3. Certification par Hub")
    p.setFont("Helvetica", 11)
    y -= 0.8*cm
    p.drawString(2*cm, y, "Chaque hub est certifié individuellement sur sa capacité à optimiser ses rails.")
    p.drawString(2*cm, y-0.6*cm, "Casablanca (48 rails) demande une gestion plus fine que Oujda (12 rails).")
    
    p.showPage()
    p.save()
    print(f"PDF généré avec succès : {os.path.abspath(file_path)}")

if __name__ == "__main__":
    generate_static_methodology()
