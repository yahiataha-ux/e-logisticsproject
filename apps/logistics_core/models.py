from django.db import models
from apps.authentication.models import User

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    capacity = models.IntegerField()
    total_rails = models.IntegerField(default=12)
    total_shelves = models.IntegerField(default=8)

    def __str__(self):
        return self.name

    def get_dynamic_image(self):
        # Specific tags for warehouses to avoid random nature shots
        return f"https://loremflickr.com/800/600/warehouse,industrial,logistics?lock={self.id}"

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    price = models.FloatField()
    stock = models.IntegerField()
    co2_impact = models.FloatField(help_text="kg CO2 per delivery")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', limit_choices_to={'role': 'Entreprise'})
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Storage details
    rail = models.IntegerField(default=1, help_text="Aisle/Rack number")
    shelf = models.IntegerField(default=1, help_text="Shelf level")

    def __str__(self):
        return self.name

    def get_dynamic_image(self):
        import re
        # Remove bracketed codes like [R17-S11]
        clean_name = re.sub(r'\[.*?\]', '', self.name).strip()
        
        # Primary tag translation (French to English for better image matching)
        fr_to_en = {
            "moteur": "motor",
            "couscous": "couscous",
            "poterie": "pottery",
            "laine": "wool",
            "tapis": "carpet",
            "carte": "electronics",
            "capteur": "sensor",
            "processeur": "cpu",
            "engrais": "fertilizer",
            "satin": "silk",
            "huile": "oil",
            "miel": "honey"
        }
        
        first_word = clean_name.split()[0].lower()
        tag = fr_to_en.get(first_word, first_word)
        
        # Category fallbacks for context
        cat_tags = {
            "Agro": "food",
            "Textile": "textile",
            "Industrie": "industrial",
            "Tech": "technology"
        }
        
        # Combine tag and category for focus
        final_tags = f"{tag},{cat_tags.get(self.category, 'product')}"
        return f"https://loremflickr.com/800/600/{final_tags}?lock={self.id}"
