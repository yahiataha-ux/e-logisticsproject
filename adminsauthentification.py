import os
import django
import sys

# Ce fichier est devenu obsolete au profit de professional_demo_seed.py
# Nous le mettons a jour pour qu'il serve de raccourci vers la nouvelle simulation.

print("--- Redirection vers professional_demo_seed.py ---")
from professional_demo_seed import seed_demo

if __name__ == "__main__":
    seed_demo()
