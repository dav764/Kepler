import json
import pandas as pd
from bs4 import BeautifulSoup
import re
import os # Ajout de la bibliothèque 'os' pour manipuler les chemins de fichiers

def update_kepler_html(html_path, csv_path, output_path, dataset_label):
    """
    Met à jour un fichier HTML Kepler.gl avec de nouvelles données CSV.
    """
    try:
        # --- 1. Lecture du fichier CSV ---
        print(f"Lecture du fichier CSV : {csv_path}")
        df = pd.read_csv(csv_path, encoding='latin-1', sep=',')

        # Conversion du DataFrame pour Kepler.gl
        new_all_data = [df.columns.tolist()] + df.values.tolist()
        new_fields = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                field_type = 'integer' if pd.api.types.is_integer_dtype(df[col]) else 'real'
            else:
                field_type = 'string'
            new_fields.append({'name': col, 'type': field_type})
        print(f"Données CSV lues et converties : {len(new_all_data) - 1} lignes.")

        # --- 2. Lecture du fichier HTML ---
        print(f"Lecture du fichier HTML : {html_path}")
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # --- 3. Extraction des données existantes ---
        script_tag = soup.find('script', string=re.compile(r'function customize\(keplerGl, store\)'))
        if not script_tag:
            raise ValueError("Impossible de trouver le bloc <script> de configuration dans le HTML.")
        
        script_content = script_tag.string
        datasets_match = re.search(r'const datasets = (\[.*?\]);', script_content, re.DOTALL)
        if not datasets_match:
            raise ValueError("Impossible d'extraire la variable 'datasets' du HTML.")
        
        datasets_str = datasets_match.group(1)
        map_datasets = json.loads(datasets_str)
        print("Données existantes extraites du HTML.")

        # --- 4. Remplacement du dataset CSV ---
        csv_found = False
        for dataset in map_datasets:
            label = dataset.get('info', {}).get('label') or dataset.get('data', {}).get('label')
            if label == dataset_label:
                print(f"Dataset '{dataset_label}' trouvé. Remplacement des données...")
                dataset['data']['allData'] = new_all_data
                dataset['data']['fields'] = new_fields
                csv_found = True
                break
        
        if not csv_found:
            raise ValueError(f"Le dataset '{dataset_label}' n'a pas été trouvé dans le HTML.")

        # --- 5. Réinjection des données mises à jour ---
        updated_datasets_str = json.dumps(map_datasets, separators=(',', ':'))
        updated_script_content = script_content.replace(datasets_str, updated_datasets_str, 1)
        script_tag.string.replace_with(updated_script_content)

        # --- 6. Sauvegarde du nouveau fichier HTML ---
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"\n🎉 Succès ! Fichier mis à jour sauvegardé ici : {output_path}")

    except FileNotFoundError as e:
        print(f"\nERREUR : Fichier non trouvé - {e}")
    except Exception as e:
        print(f"\nERREUR : Une erreur est survenue - {e}")

# --- POINT D'ENTRÉE DU SCRIPT ---
if __name__ == '__main__':
    # --- Configuration Simplifiée ---
    # Vous n'avez plus que 3 chemins à vérifier.
    
    # 1. Le fichier HTML original qui sert de modèle
    HTML_SOURCE_PATH = 'index.html'
    
    # 2. Le fichier CSV avec les données mises à jour
    CSV_SOURCE_PATH = 'flow_final.csv'
    
    # 3. Le fichier HTML final qui sera généré
    HTML_OUTPUT_PATH = 'index.html'

    # --- Exécution ---
    # Le nom du dataset à remplacer est maintenant déduit automatiquement du chemin du fichier CSV.
    # Plus besoin de le définir manuellement !
    dataset_label_to_find = os.path.basename(CSV_SOURCE_PATH)
    
    update_kepler_html(HTML_SOURCE_PATH, CSV_SOURCE_PATH, HTML_OUTPUT_PATH, dataset_label_to_find)
