import glob
import os
import pandas as pd
import re 
def main(): 
    dossier_source = os.path.dirname(os.path.abspath(__file__))

    ### get all files 
    fichiers_gz = sorted(glob.glob(os.path.join(dossier_source, "icu/*.csv.gz")))
    fichiers_gz += sorted(glob.glob(os.path.join(dossier_source, "hosp/*.csv.gz")))


    def afficher_resume(nom_fichier, dataframe):
        """Affiche les informations principales d'un dataset."""
        valeurs_manquantes = dataframe.isna().sum()
        valeurs_manquantes = valeurs_manquantes[valeurs_manquantes > 0].sort_values(ascending=False)

        print(f"\n{'=' * 80}")
        print(f"Dataset : {nom_fichier}")
        print(f"Dimensions : {dataframe.shape[0]:,} lignes x {dataframe.shape[1]} colonnes")
        print(f"Colonnes : {', '.join(dataframe.columns)}")
        if valeurs_manquantes.empty:
            print("Valeurs manquantes : aucune")
        else:
            print("Valeurs manquantes (maximum 10 colonnes) :")
            print(valeurs_manquantes.head(10).to_string())
        print("\nAperçu des 5 premières lignes :")
        print(dataframe.head().to_string(index=False))

    liste_df = []
    for fichier in fichiers_gz:
        df_temp = pd.read_csv(fichier)
        afficher_resume(os.path.basename(fichier), df_temp)
        liste_df.append(df_temp)

    if liste_df:
        df_final = pd.concat(liste_df, ignore_index=True)
        print(f"\nFusion réussie ! Dimensions totales : {df_final.shape}")
    else:
        print("Aucun fichier .csv.gz trouvé dans ce répertoire.")

def check_d_items(source_file, item_ids):
    source_path = source_file
    source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), source_path)

    df = pd.read_csv(source_path)
    if not isinstance(item_ids, (list, tuple, set)):
        item_ids = [item_ids]
    df = df[df["itemid"].isin(item_ids)]
    print("Action successful")

def get_wanted_patients(source_file,item_ids):
    ##Get the correct file path
    source_path = source_file
    source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), source_path)
    df = pd.read_csv(source_path)
    if not isinstance(item_ids, (list, tuple, set)):
        item_ids = [item_ids]
    df = df[df["itemid"].isin(item_ids)]
    # df = df[df["storetime"] < 4*60 ] // check time unit make it less than 4 hours after admission
    store_time = pd.to_datetime(df["storetime"])
    df = df[ store_time.dt.hour < 4]
     
    print(store_time)
    print(df.head())
    print(df.head(50))
    print("Action successful")


if __name__ == "__main__" : 
    check_d_items("icu/d_items.csv.gz",[220045,220210,220277])
    get_wanted_patients("icu/chartevents.csv.gz", [22045,220210,220277])