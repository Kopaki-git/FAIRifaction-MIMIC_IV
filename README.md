# FAIRifaction-MIMIC_IV

Scripts for exploring the FAIRification of MIMIC-IV.

## Structure

Les fichiers MIMIC-IV doivent rester dans les dossiers `data/icu/` et
`data/hosp/`. Le script `src/explore_data.py` résout ces chemins depuis la
racine du projet, quel que soit le dossier courant.

## Installation

```bash
python3 -m pip install pandas
```

## Execution

Depuis la racine du projet :

```bash
python3 src/explore_data.py
```
