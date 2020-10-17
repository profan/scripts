from collections import namedtuple
import csv
import os

import pandas as pd
import util

# contig id may look like 58282 but also 28582_5929_etc
def get_leading_id(s):
    return s.split("_", 1)[0]

def collect_proteins_from_file(path):
    data = pd.read_csv(path, sep='\t')
    without_hypotheticals = data.query('function.str.contains("hypothetical") == False')
    return without_hypotheticals

def collect_subsystems_from_file_pandas(path):
    data = pd.read_csv(path, sep='\t')
    with_only_unique_roles = data.groupby('Role').first().reset_index()
    return with_only_unique_roles

def filter_for_files(path, ext, pattern):
    matched_files = util.get_files_in_folder_with_ext(path, ext)
    return [f for f in matched_files if pattern in f]

def file_path_to_id(path):
    return ''.join(filter(str.isdigit, path))

def collect_proteins_from_all_files(path):
    filtered_tsv_files = filter_for_files(path = path, ext = '.tsv', pattern = 'rast_proteins')
    return [(file_path_to_id(f), collect_proteins_from_file(f)) for f in filtered_tsv_files]

def collect_subsystems_from_all_files(path):
    filtered_tsv_files = filter_for_files(path = path, ext = '.tsv', pattern = 'rast_subsystems')
    return [(file_path_to_id(f), collect_subsystems_from_file_pandas(f)) for f in filtered_tsv_files]

predation_data = pd.read_csv('../data/k_pneumoniae_predation.csv')
susceptible = predation_data.query('Susceptibility == "S"')
resistant = predation_data.query('Susceptibility == "R"')

all_protein_data = collect_proteins_from_all_files('../output')
susceptible_samples = [(id, data) for (id, data) in all_protein_data if len(susceptible.query('Number == @id')) > 0]
resistant_samples = [(id, data) for (id, data) in all_protein_data if len(resistant.query('Number == @id')) > 0]

susceptible_proteins = pd.concat([data for (id, data) in susceptible_samples])
resistant_proteins = pd.concat([data for (id, data) in resistant_samples])

all_proteins = pd.concat([susceptible_proteins, resistant_proteins])
all_common_proteins = all_proteins.query('function in @susceptible_proteins.function and function in @resistant_proteins.function')

all_proteins_unique_to_susceptible = all_proteins.query('function in @susceptible_proteins.function and function not in @all_common_proteins.function')
all_proteins_unique_to_resistant = all_proteins.query('function in @resistant_proteins.function and function not in @all_common_proteins.function')

print(f"number of classified proteins unique to susceptible samples: {len(all_proteins_unique_to_susceptible)}")
print(f"number of classified proteins unique to resistant samples: {len(all_proteins_unique_to_resistant)}")