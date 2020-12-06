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
predation_data.columns = [c.replace(' ', '_') for c in predation_data.columns]

is_susceptible = "Log_reduction == '3' or Log_reduction == '4' or Log_reduction == '5'"
is_resistant = "Log_reduction == '0' or Log_reduction == '1' or Log_reduction == '2'"
# is_intermediate = "Log_reduction > 999"

susceptible = predation_data.query(is_susceptible)
resistant = predation_data.query(is_resistant)

# intermediate = predation_data.query(is_intermediate)

all_protein_data = collect_proteins_from_all_files('../output')
susceptible_samples = [(id, data) for (id, data) in all_protein_data if len(susceptible.query('Number == @id')) > 0]
resistant_samples = [(id, data) for (id, data) in all_protein_data if len(resistant.query('Number == @id')) > 0]
# intermediate_samples = [(id, data) for (id, data) in all_protein_data if len(intermediate.query('Number == @id')) > 0]

susceptible_proteins = pd.concat([data for (id, data) in susceptible_samples]) \
    .drop_duplicates(subset = 'function', keep = 'first')

resistant_proteins = pd.concat([data for (id, data) in resistant_samples]) \
    .drop_duplicates(subset = 'function', keep = 'first')

# intermediate_proteins = pd.concat([data for (id, data) in intermediate_samples]) \
#     .drop_duplicates(subset = 'function', keep = 'first')

all_proteins = pd.concat([susceptible_proteins, resistant_proteins]) \
    .drop_duplicates(subset = 'function', keep = 'first')

# all_proteins.drop(all_proteins[])

import functools
all_functions = [e['function'].values.tolist() for (id, e) in all_protein_data]
all_roles = functools.reduce(lambda x, y: set(x).intersection(y), all_functions)

all_common_proteins = all_proteins.query('function in @all_roles')
# all_common_proteins = all_proteins.query('function in @susceptible_proteins.function and function in @resistant_proteins.function') \
#     .drop_duplicates(subset = 'function', keep = 'first')

print(f"number of total proteins: {len(all_proteins)}")
print(f"number of common proteins: {len(all_common_proteins)}")

number_of_unique_functions_in_total = len(all_common_proteins.function.unique())
print(f"number of unique functions in whole dataset: {number_of_unique_functions_in_total}")
# all_protein_roles = all_proteins['function']

all_proteins_unique_to_susceptible = all_proteins.query(
    'function in @susceptible_proteins.function and function not in @resistant_proteins.function and function not in @all_common_proteins.function'
)
all_proteins_unique_to_resistant = all_proteins.query(
    'function in @resistant_proteins.function and function not in @susceptible_proteins.function and function not in @all_common_proteins.function'
)
# all_proteins_unique_to_intermediate = all_proteins.query('function in @intermediate_proteins.function and function not in @all_common_proteins.function')

# import functools
# total_number_of_proteins = functools.reduce(lambda acc, cur: acc + (len(cur[1])), all_protein_data, 0)
# average_number_of_proteins_per_sample = total_number_of_proteins / len(all_protein_data)
# print(f"average number of proteins per sample: {average_number_of_proteins_per_sample}")

print(f"number of classified proteins unique to susceptible samples: {len(all_proteins_unique_to_susceptible)}")
print(f"number of classified proteins unique to resistant samples: {len(all_proteins_unique_to_resistant)}")
# print(f"number of classified proteins unique to intermediate samples: {len(all_proteins_unique_to_intermediate)}")

# s_i_overlap = all_proteins.query('function in @susceptible_proteins and function in @intermediate_proteins')
# r_i_overlap = all_proteins.query('function in @resistant_proteins and function in @intermediate_proteins')
s_r_overlap = all_proteins.query('function in @susceptible_proteins and function in @resistant_proteins and function not in @all_common_proteins.function')

# calculate the ones common to log reduction 2 or 3
log2_data = predation_data.query('Log_reduction == "2"')
log2_samples = [(id, data) for (id, data) in all_protein_data if len(log2_data.query('Number == @id')) > 0]
log2_proteins = pd.concat([data for (id, data) in log2_samples])
log2_proteins = log2_proteins.query('function not in @all_common_proteins.function') \
        .drop_duplicates(subset = 'function', keep = 'first')

log3_data = predation_data.query('Log_reduction == "3"')
log3_samples = [(id, data) for (id, data) in all_protein_data if len(log3_data.query('Number == @id')) > 0]
log3_proteins = pd.concat([data for (id, data) in log3_samples])
log3_proteins = log3_proteins.query('function not in @all_common_proteins.function') \
        .drop_duplicates(subset = 'function', keep = 'first')

log2_3_similarity = min(len(log2_proteins), len(log3_proteins)) / max(len(log2_proteins), len(log3_proteins))
print(f"similarity between log2 and log3 reduction data: {log2_3_similarity * 100.0} %")

num_s = len(susceptible_proteins)
num_r = len(resistant_proteins)
# num_i = len(intermediate_proteins)

# s_i_similarity = min(num_s, num_i) / max(num_s, num_i)
# r_i_similarity = min(num_r, num_i) / max(num_r, num_i)
s_r_similarity = min(num_s, num_r) / max(num_s, num_r)

# print(f"similarity in protein make-up between S and I: {s_i_similarity * 100.0} %")
# print(f"similarity in protein make-up between R and I: {r_i_similarity * 100.0} %")
print(f"similarity in protein make-up between S and R: {s_r_similarity * 100.0} %")
# print(f"percentage of hypothetical proteins: {}")

def output_to_file(data, output_filename):
    print(f"output common proteins to {output_filename}")
    with open(f"{output_filename}.csv", 'w') as f:
        f.write(data.to_csv())

output_to_file(all_common_proteins, 'all_common_proteins')
output_to_file(all_proteins_unique_to_resistant, 'unique_resistant_proteins')
output_to_file(all_proteins_unique_to_susceptible, 'unique_susceptible_roteins')
# output_to_file(all_proteins_unique_to_intermediate, 'unique_intermediate_proteins')
