from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def resolve_data_path(source_file: str | Path) -> Path:
    """Resolve a dataset path relative to the project's data directory."""
    source_path = Path(source_file)
    if source_path.parts and source_path.parts[0] == "data":
        source_path = Path(*source_path.parts[1:])

    resolved_path = DATA_DIR / source_path
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Dataset introuvable : {resolved_path}")
    return resolved_path


def main() -> None:
    ### goes in folder and detects all csv.gz files
    gz_files = sorted(DATA_DIR.glob("*/**/*.csv.gz"))


    def data_visual(file_name, dataframe):
        """Give main information from all the csv files in data files."""
        missing_values = dataframe.isna().sum()
        missing_values = missing_values[missing_values > 0].sort_values(ascending=False)

        print(f"\n{'=' * 80}")
        print(f"Dataset : {file_name}")
        print(f"Dimensions : {dataframe.shape[0]:,} lignes x {dataframe.shape[1]} colonnes")
        print(f"Columns : {', '.join(dataframe.columns)}")
        if missing_values.empty:
            print("No missing values")
        else:
            print("Extract of missing values (5 values)")
            print(missing_values.head().to_string())
        print("\nAperçu des 5 premières lignes :")
        print(dataframe.head().to_string(index=False))

    csv_list = []
    for fichier in gz_files:
        df_temp = pd.read_csv(fichier)
        data_visual(fichier.relative_to(DATA_DIR), df_temp)
        csv_list.append(df_temp)

    # if csv_list:
    #     df_final = pd.concat(csv_list, ignore_index=True)
    #     print(f"\n Successful concat, total dimensions : {df_final.shape}")
    # else:
    #     print("no files detected")

def check_d_items(source_file: str | Path, item_ids: list[int] | tuple[int, ...] | set[int]) -> pd.DataFrame:
    df = pd.read_csv(resolve_data_path(source_file))
    if not isinstance(item_ids, (list, tuple, set)):
        item_ids = [item_ids]
    df = df[df["itemid"].isin(item_ids)]
    print("Action done")
    return df


def get_wanted_patients(source_file: str | Path, item_ids: list[int] | tuple[int, ...] | set[int]) -> pd.DataFrame:
    df = pd.read_csv(resolve_data_path(source_file))
    if not isinstance(item_ids, (list, tuple, set)):
        item_ids = [item_ids]
    df = df[df["itemid"].isin(item_ids)]
    store_time = pd.to_datetime(df["storetime"])
    df = df[store_time.dt.hour < 4]

    print(df.head(50))
    print("Action successful")
    return df


if __name__ == "__main__":
    check_d_items("icu/d_items.csv.gz", [220045, 220210, 220277])
    get_wanted_patients("icu/chartevents.csv.gz", [220045, 220210, 220277])