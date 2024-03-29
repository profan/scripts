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
    with_only_unique_roles = data.groupby('Role').first().reset_index().rename(columns={'Role':'function'})
    return with_only_unique_roles

def filter_for_files(path, ext, pattern):
    matched_files = util.get_files_in_folder_with_ext(path, ext)
    return [f for f in matched_files if pattern in f]

def file_path_to_id(path):
    return ''.join(filter(str.isdigit, path))

def merge_dataframes_on_column(frames, how, on):
    df_merge_result = frames[0]
    for df in frames[1:]:
        df_merge_result = pd.merge(
            df_merge_result, df.drop_duplicates(subset = 'function', keep='first'),
            how=how,
            on=on
        )
    return df_merge_result

def collect_combined_protein_data_from_all_files(path):

    filtered_tsv_files = filter_for_files(path = path, ext = '.tsv', pattern = 'rast_proteins')
    # the_merged_dataframes = [(file_path_to_id(f), merge_dataframes_on_column([collect_proteins_from_file(f), collect_subsystems_from_file_pandas(f"

    output_combined_data_frames = []
    for f in filtered_tsv_files:
        subsystem_filename = f.replace("rast_proteins.tsv", "rast_subsystems.tsv")
        output_combined_data_frames.append(
            (file_path_to_id(f), # collect_proteins_from_file(f))
            merge_dataframes_on_column(
                [collect_proteins_from_file(f), collect_subsystems_from_file_pandas(subsystem_filename)], how='inner', on=['function']
            ))
        )

    return output_combined_data_frames

def collect_proteins_from_all_files(path):
    filtered_tsv_files = filter_for_files(path = path, ext = '.tsv', pattern = 'rast_proteins')
    return [(file_path_to_id(f), collect_proteins_from_file(f)) for f in filtered_tsv_files]

def collect_subsystems_from_all_files(path):
    filtered_tsv_files = filter_for_files(path = path, ext = '.tsv', pattern = 'rast_subsystems')
    return [(file_path_to_id(f), collect_subsystems_from_file_pandas(f)) for f in filtered_tsv_files]

predation_data = pd.read_csv('../data/k_pneumoniae_predation.csv')
predation_data.columns = [c.replace(' ', '_') for c in predation_data.columns]

# 2021-04-02: we previously grouped intermediates in with resistants, but had forgotten why
#  and so we now reintroduce the intermediates group.. at least until we figure out why we did that before :P
is_susceptible = "Log_reduction == '3' or Log_reduction == '4' or Log_reduction == '5' or Log_reduction == '2'"
is_resistant = "Log_reduction == '0' or Log_reduction == '1'"
is_intermediate = "Log_reduction == '2'"

susceptible = predation_data.query(is_susceptible)
resistant = predation_data.query(is_resistant)
intermediate = predation_data.query(is_intermediate)

is_alisa = False
if is_alisa:
    output_path = '../output/alisa'
else:
    output_path = '../output'

# collect_combined_protein_data_from_all_files(output_path)
# all_protein_data = collect_proteins_from_all_files(output_path)
all_protein_data = collect_combined_protein_data_from_all_files(output_path)
all_subsystem_data = collect_subsystems_from_all_files(output_path)
# subsystem_data_frame = pd.concat([data for (id, data) in all_subsystem_data]) \
#    .drop_duplicates(subset = 'Role', keep = 'first') # this might drop useful data if we want to know all the locations a given role occurs, this will just give us the first
    # .rename(columns={'Role':'function'})

susceptible_samples = [(id, data) for (id, data) in all_protein_data if len(susceptible.query('Number == @id')) > 0]
resistant_samples = [(id, data) for (id, data) in all_protein_data if len(resistant.query('Number == @id')) > 0]
intermediate_samples = [(id, data) for (id, data) in all_protein_data if len(intermediate.query('Number == @id')) > 0]

unique_merge_column = 'function'
unique_key_column = 'Subsystem'
# unique_key_column = 'Subsystem'

susceptible_proteins = pd.concat([data for (id, data) in susceptible_samples]) \
    .drop_duplicates(subset = unique_merge_column, keep = 'first')

susceptible_proteins_common = merge_dataframes_on_column([data for (id, data) in susceptible_samples], how='inner', on=[unique_merge_column]) \
    .drop_duplicates(subset = unique_merge_column, keep = 'first')

resistant_proteins = pd.concat([data for (id, data) in resistant_samples]) \
    .drop_duplicates(subset = unique_merge_column, keep = 'first')

resistant_proteins_common = merge_dataframes_on_column([data for (id, data) in resistant_samples], how='inner', on=[unique_merge_column]) \
    .drop_duplicates(subset = unique_merge_column, keep = 'first')

print(resistant_proteins_common)
exit(-1)

# intermediate_proteins = pd.concat([data for (id, data) in intermediate_samples]) \
#.drop_duplicates(subset = 'function', keep = 'first')

# intermediate_proteins_common = merge_dataframes_on_column([data for (id, data) in intermediate_samples], how='inner', on=['function']) \
#     .drop_duplicates(subset = 'function', keep = 'first')

all_proteins = pd.concat([susceptible_proteins, resistant_proteins]) \
    .drop_duplicates(subset = unique_merge_column, keep = 'first')

# all_proteins.drop(all_proteins[])

import functools
all_functions = [e[unique_key_column].values.tolist() for (id, e) in all_protein_data]
all_roles = functools.reduce(lambda x, y: set(x).intersection(y), all_functions)

all_common_proteins = all_proteins.query(f"{unique_key_column} in @all_roles")
# all_common_proteins = all_proteins.query('function in @susceptible_proteins.function and function in @resistant_proteins.function') \
#     .drop_duplicates(subset = 'function', keep = 'first')

print(f"number of total proteins: {len(all_proteins)}")
print(f"number of common proteins: {len(all_common_proteins)}")

number_of_unique_functions_in_total = len(all_common_proteins.function.unique())
print(f"number of unique {unique_key_column}s in whole dataset: {number_of_unique_functions_in_total}")
# all_protein_roles = all_proteins['function']

# if it occurs in any samples in the group but not in any other groups
all_proteins_unique_to_susceptible = all_proteins.query(
    f"{unique_key_column} in @susceptible_proteins.{unique_key_column} and {unique_key_column} not in @resistant_proteins.{unique_key_column} and {unique_key_column} not in @all_common_proteins.{unique_key_column}"
)
all_proteins_unique_to_resistant = all_proteins.query(
    f"{unique_key_column} in @resistant_proteins.{unique_key_column} and {unique_key_column} not in @susceptible_proteins.{unique_key_column} and {unique_key_column} not in @all_common_proteins.{unique_key_column}"
)
# all_proteins_unique_to_intermediate = all_proteins.query(
#     'function in @intermediate_proteins.function and function not in @resistant_proteins.function and function not in @susceptible_proteins.function and function not in @all_common_proteins.function'
# )

# new set of those that only occur in _all samples_ within the group
all_proteins_unique_to_every_susceptible = all_proteins.query(
    f"{unique_key_column} in @susceptible_proteins_common.{unique_key_column} and {unique_key_column} not in @resistant_proteins_common.{unique_key_column} and {unique_key_column} not in @all_common_proteins.{unique_key_column}"
)
all_proteins_unique_to_every_resistant = all_proteins.query(
    f"{unique_key_column} in @resistant_proteins_common.{unique_key_column} and {unique_key_column} not in @susceptible_proteins_common.{unique_key_column} and {unique_key_column} not in @all_common_proteins.{unique_key_column}"
)
#all_proteins_unique_to_every_intermediate = all_proteins.query(
#    'function in @intermediate_proteins_common.function and function not in @resistant_proteins_common.function and function not in @susceptible_proteins_common.function and function not in @all_common_proteins.function'
# )

# import functools
# total_number_of_proteins = functools.reduce(lambda acc, cur: acc + (len(cur[1])), all_protein_data, 0)
# average_number_of_proteins_per_sample = total_number_of_proteins / len(all_protein_data)
# print(f"average number of proteins per sample: {average_number_of_proteins_per_sample}")

print(f"number of classified proteins unique to susceptible samples: {len(all_proteins_unique_to_susceptible)}")
print(f"number of classified proteins unique to resistant samples: {len(all_proteins_unique_to_resistant)}")
# print(f"number of classified proteins unique to intermediate samples: {len(all_proteins_unique_to_intermediate)}")

# s_i_overlap = all_proteins.query('function in @susceptible_proteins and function in @intermediate_proteins')
# r_i_overlap = all_proteins.query('function in @resistant_proteins and function in @intermediate_proteins')
s_r_overlap = all_proteins.query(
    f"{unique_key_column} in @susceptible_proteins and {unique_key_column} in @resistant_proteins and {unique_key_column} not in @all_common_proteins.{unique_key_column}"
)

# calculate the ones common to log reduction 2 or 3
# log2_data = predation_data.query('Log_reduction == "2"')
# log2_samples = [(id, data) for (id, data) in all_protein_data if len(log2_data.query('Number == @id')) > 0]
# log2_proteins = pd.concat([data for (id, data) in log2_samples])
# log2_proteins = log2_proteins.query('function not in @all_common_proteins.function') \
#         .drop_duplicates(subset = 'function', keep = 'first')

log3_data = predation_data.query('Log_reduction == "3"')
log3_samples = [(id, data) for (id, data) in all_protein_data if len(log3_data.query('Number == @id')) > 0]
log3_proteins = pd.concat([data for (id, data) in log3_samples])
log3_proteins = log3_proteins.query(f"{unique_key_column} not in @all_common_proteins.{unique_key_column}") \
        .drop_duplicates(subset = unique_key_column, keep = 'first')

# log2_3_similarity = min(len(log2_proteins), len(log3_proteins)) / max(len(log2_proteins), len(log3_proteins))
# print(f"similarity between log2 and log3 reduction data: {log2_3_similarity * 100.0} %")

num_s = len(susceptible_proteins)
num_r = len(resistant_proteins)
# num_i = len(intermediate_proteins)

num_s_common = len(susceptible_proteins_common)
num_r_common = len(resistant_proteins_common)
# num_i_common = len(intermediate_proteins_common)
print(f"num_s_common: {num_s_common}")
print(f"num_r_common: {num_r_common}")
# print(f"num_i_common: {num_i_common}")

num_u_s_common = len(all_proteins_unique_to_every_susceptible)
num_u_r_common = len(all_proteins_unique_to_every_resistant)
# num_u_i_common = len(all_proteins_unique_to_every_intermediate)
print(f"num_u_s_common: {num_u_s_common}")
print(f"num_u_r_common: {num_u_r_common}")
# print(f"num_u_i_common: {num_u_i_common}")

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

output_to_path = "s_plus_i_vs_r"
output_to_file(all_common_proteins, os.path.join(output_to_path, 'all_common_proteins'))
output_to_file(all_proteins_unique_to_resistant, os.path.join(output_to_path, 'unique_resistant_proteins'))
output_to_file(all_proteins_unique_to_susceptible, os.path.join(output_to_path, 'unique_susceptible_proteins'))
# output_to_file(all_proteins_unique_to_intermediate, 'unique_intermediate_proteins')

output_to_file(all_proteins_unique_to_every_resistant, os.path.join(output_to_path, 'unique_resistant_proteins_common'))
output_to_file(all_proteins_unique_to_every_susceptible, os.path.join(output_to_path, 'unique_susceptible_proteins_common'))
# output_to_file(all_proteins_unique_to_every_intermediate, 'unique_intermediate_proteins_common')
