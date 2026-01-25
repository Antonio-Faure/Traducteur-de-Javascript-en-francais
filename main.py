import re
from mistralai import Mistral
from datetime import datetime
import time
import subprocess
import json
import tempfile
import os

# Initialisation du client Mistral
api_key = "YOUR_MISTRAL_API_KEY"  # À remplacer par ta clé API
client = Mistral(api_key=api_key)
model = "mistral-small-latest"


def formater_javascript(contenu_js):
    """Formate le code JavaScript avec Prettier ou manuellement"""
    try:
        # Essayer avec prettier (si installé)
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.js', delete=False) as f:
            f.write(contenu_js)
            f.flush()
            result = subprocess.run(['prettier', '--write', f.name], capture_output=True, text=True)
            if result.returncode == 0:
                with open(f.name, 'r') as formatted_file:
                    return formatted_file.read()
            else:
                return contenu_js
    except FileNotFoundError:
        return contenu_js


def extraire_chaines(contenu_js):
    """Extrait les chaînes de caractères du code JavaScript"""
    return re.findall(r'[\'\"](.*?)[\'\"]', contenu_js)


def traduire_texte(texte):
    """Traduit un texte en français en utilisant l'API Mistral"""
    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "user", "content": f"Traduis ce texte en français, en gardant le même style et le même ton : {texte}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return texte


def traduire_code_js(contenu_js):
    """Traduit les chaînes de caractères d'un code JavaScript"""
    chaine_originale = extraire_chaines(contenu_js)
    chaine_traduite = [traduire_texte(texte) for texte in chaine_originale]
    
    # Remplacer les chaînes originales par les traduites
    for originale, traduite in zip(chaine_originale, chaine_traduite):
        contenu_js = contenu_js.replace(f'"{originale}"', f'"{traduite}"')
        contenu_js = contenu_js.replace(f"'{originale}'", f"'{traduite}'")
    
    return contenu_js


if __name__ == "__main__":
    # Exemple d'utilisation
    exemple_js = '''
    function saluer() {
        console.log("Hello, world!");
        alert('Welcome to our website!');
    }
    '''
    
    print("Code original :")
    print(exemple_js)
    
    js_formate = formater_javascript(exemple_js)
    js_traduit = traduire_code_js(js_formate)
    
    print("\nCode traduit :")
    print(js_traduit)