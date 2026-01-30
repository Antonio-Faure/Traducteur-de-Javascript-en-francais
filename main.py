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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(contenu_js)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['npx', 'prettier', '--write', temp_file],
                capture_output=True,
                timeout=10
            )
            
            with open(temp_file, 'r') as f:
                contenu_formate = f.read()
            
            os.unlink(temp_file)
            print("✨ Code formaté avec Prettier")
            return contenu_formate
        except:
            os.unlink(temp_file)
            # Si prettier échoue, utiliser le formatage manuel
            print("⚠️  Prettier non disponible, utilisation du formatage manuel")
            return formater_javascript_manuel(contenu_js)
            
    except Exception as e:
        print(f"⚠️  Prettier non disponible, utilisation du formatage manuel")
        return formater_javascript_manuel(contenu_js)


def formater_javascript_manuel(contenu_js):
    """Formate le code JavaScript manuellement"""
    lines = contenu_js.split('\n')
    formatted_lines = []
    indent_level = 0
    indent_str = "  "  # 2 espaces
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            formatted_lines.append('')
            continue
        
        # Réduire l'indentation pour les } et )
        if stripped.startswith('}') or stripped.startswith(']') or stripped.startswith(')'):
            indent_level = max(0, indent_level - 1)
        
        # Ajouter la ligne avec l'indentation correcte
        formatted_lines.append(indent_str * indent_level + stripped)
        
        # Augmenter l'indentation pour les { et [
        if stripped.endswith('{') or stripped.endswith('[') or stripped.endswith('('):
            indent_level += 1
        
        # Gérer les cas où { et } sont sur la même ligne
        open_count = stripped.count('{') + stripped.count('[') + stripped.count('(')
        close_count = stripped.count('}') + stripped.count(']') + stripped.count(')')
        indent_level += open_count - close_count
    
    return '\n'.join(formatted_lines)


def extraire_chaines_avec_lignes(contenu_js):
    """Extrait toutes les chaînes de caractères avec la ligne complète"""
    # Regex pour capturer les chaînes entre guillemets simples et doubles
    pattern = r'''(['"`])([^'"`]*?)\1'''
    
    lines = contenu_js.split('\n')
    chaines = []
    position_globale = 0
    
    for num_ligne, ligne in enumerate(lines, 1):
        matches = re.finditer(pattern, ligne)
        
        for match in matches:
            quote_type = match.group(1)
            contenu = match.group(2)
            
            chaines.append({
                'original': match.group(0),
                'contenu': contenu,
                'quote': quote_type,
                'position': position_globale + match.start(),
                'ligne': ligne.strip(),
                'numero_ligne': num_ligne
            })
        
        position_globale += len(ligne) + 1  # +1 pour le \n
    
    return chaines


def est_du_texte_a_traduire(chaine, contexte="", ligne_complete=""):
    """Demande à Mistral si la chaîne est du texte à traduire"""
    
    prompt = f"""Est-ce que cette chaîne est du texte visible à traduire pour l'utilisateur final? 
(pas du code, pas une clé API, pas une URL, pas un identifiant technique)
Attention, "button" seul n'est pas du texte.

Chaîne à analyser: "{chaine}"

Ligne de code complète:
{ligne_complete}

Contexte du projet: {contexte}

Réponds UNIQUEMENT par: true ou false"""
    
    debut_req = datetime.now()
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )
    fin_req = datetime.now()
    
    reponse = chat_response.choices[0].message.content.strip().lower()
    return 'true' in reponse


def traduire_texte(texte, contexte="", ligne_complete=""):
    """Traduit le texte en français avec Mistral"""
    
    prompt = f"""Traduis cette chaîne en français. Garde le même ton et le même style.

Chaîne à traduire: "{texte}"

Contexte du code: {ligne_complete}

Contexte du projet: {contexte}

Réponds UNIQUEMENT par la traduction en français, sans guillemets ni explications."""
    
    debut = datetime.now()
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )
    fin = datetime.now()
    
    texte_traduit = chat_response.choices[0].message.content.strip()
    return texte_traduit


def traiter_fichier_javascript(chemin_fichier, contexte=""):
    """Traite un fichier JavaScript complet"""
    
    # Lire le fichier
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        contenu_original = f.read()
    
    print(f"📄 Lecture du fichier: {chemin_fichier}")
    
    # Formater le code
    contenu_formate = formater_javascript(contenu_original)
    
    # Extraire les chaînes
    chaines = extraire_chaines_avec_lignes(contenu_formate)
    print(f"✅ {len(chaines)} chaînes trouvées")
    print(f"⏱️  Temps estimé: {len(chaines) * 2} secondes (2 requêtes par chaîne)\n")
    
    contenu_modifie = contenu_formate
    traductions = []
    debut_total = datetime.now()
    
    # Traiter chaque chaîne
    for i, chaine_info in enumerate(chaines, 1):
        texte = chaine_info['contenu']
        ligne = chaine_info['ligne']
        chaines_restantes = len(chaines) - i
        temps_restant = chaines_restantes * 2  # 2 requêtes par chaîne
        
        print(f"[{i}/{len(chaines)}] Ligne {chaine_info['numero_ligne']}: {texte}")
        print(f"    📝 {ligne}")
        print(f"    ⏱️  Chaînes restantes: {chaines_restantes} | Temps estimé: {temps_restant}s")
        
        # Vérifier si c'est du texte à traduire
        if est_du_texte_a_traduire(texte, contexte, ligne):
            print(f"  → C'est du texte!")
            
            # Attendre 1 seconde avant la deuxième requête
            time.sleep(1)
            
            # Traduire
            texte_traduit = traduire_texte(texte, contexte, ligne)
            print(f"  → Traduction: {texte_traduit}")
            
            # Mémoriser pour le remplacement
            traductions.append({
                'original': chaine_info['original'],
                'traduit': f"{chaine_info['quote']}{texte_traduit}{chaine_info['quote']}"
            })
        else:
            print(f"  → Pas du texte à traduire")
        
        # Attendre 1 seconde avant la prochaine itération (sauf à la dernière)
        if i < len(chaines):
            time.sleep(1)
        
        print()  # Ligne vide pour la lisibilité
    
    # Remplacer dans le contenu
    for traduction in traductions:
        contenu_modifie = contenu_modifie.replace(
            traduction['original'],
            traduction['traduit'],
            1  # Remplacer seulement la première occurrence
        )
    
    # Sauvegarder le fichier modifié
    fichier_sortie = chemin_fichier.replace('.js', '_traduit.js')
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(contenu_modifie)
    
    fin_total = datetime.now()
    temps_total = fin_total - debut_total
    
    print(f"\n✨ Fichier sauvegardé: {fichier_sortie}")
    print(f"📊 {len(traductions)} chaînes ont été traduites")
    print(f"⏱️  Temps total: {temps_total}")
    
    return fichier_sortie

def test():
    # Créer un fichier JavaScript de test
    test_js = '''const greeting = "Hello World";
        const apiKey = "sk_test_1234567890";
        const message = "Welcome to our application";
        const url = "https://api.example.com";
        const userName = "John Doe";
        console.log("Application started");
        function greet(name) {
        return "Hello " + name;
        }'''
    
    with open('test.js', 'w') as f:
        f.write(test_js)
    
    # Traiter le fichier
    traiter_fichier_javascript(
        'test.js',
        contexte="Application web en français"
    )


# Exemple d'utilisation
if __name__ == "__main__":
    # test()

    traiter_fichier_javascript(
        'main.js',
        contexte="Veuillez taper le contexte du javascript"
    )
