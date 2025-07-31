import os
import pandas as pd
import numpy as np
import re

def clean_entry(val):
    if pd.isna(val):
        return ''
    # Remove ALL whitespace & line breaks
    return re.sub(r'\s+', '', str(val)).upper()

def get_min_max_snr(root_dir):
    min_snr, max_snr = float('inf'), float('-inf')
    print(f"Scanning directory: {root_dir}")

    # Traverse the directory tree
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(subdir, file)
                try:
                    # Read only the first row of the CSV
                    df = pd.read_csv(file_path, nrows=1)
                    snr_values = list(df.columns[1:])  # Skip the first column which is the label
                    snr_values = list(map(float, snr_values))  # Convert to float
                    
                    # Update min and max
                    min_snr = min(min_snr, min(snr_values))
                    max_snr = max(max_snr, max(snr_values))
                except Exception as e:
                    print(f"Failed to process {file_path}: {e}")

    return min_snr, max_snr

########################################################################################################################################

def interpolate_bler(root_dir, key):

    # Step 1: Define the augmented root directory and output path

    augmented_root = os.path.expanduser(f"C:/Users/Vaideeswaran/Downloads/NRV2XSL_LinkLevelDatasetAugmented/{key}")
    os.makedirs(augmented_root, exist_ok=True)

    # Step 2: Determine global min and max SNR from all CSV headers

    root_dir = os.path.abspath(root_dir)
    min_snr, max_snr = get_min_max_snr(root_dir)
    print(f"Global min SNR: {min_snr}, Global max SNR: {max_snr}")

    # Step 3: Create the uniform SNR range (1 dB step)
    snr_range = np.arange(min_snr, max_snr + 1, 1.0)
    total_na_count = 0  # 👈 Counter for all NA entries

    # Step 4: Process all files again, and write transformed CSVs
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv"):
                path = os.path.join(subdir, file)
                try:
                    df = pd.read_csv(path)
                    snr_values = list(map(float, df.columns[1:]))
                    bler_values = df.iloc[0, 1:].astype(float).values
                    bler_dict = dict(zip(snr_values, bler_values))

                    # Create new BLER list for the full SNR range
                    new_bler = []
                    for snr in snr_range:
                        if snr in bler_dict:
                            new_bler.append(bler_dict[snr])
                        else:
                            higher = [bler_dict[s] for s in snr_values if s > snr]
                            lower = [bler_dict[s] for s in snr_values if s < snr]

                            if any(b >= 1 - 1e-4 for b in higher):
                                new_bler.append(1.0)
                            elif any(b <= 1e-4 for b in lower):
                                new_bler.append(0.0)
                            else:
                                new_bler.append("NA")
                                total_na_count += 1

                    # Build new DataFrame
                    output_df = pd.DataFrame({
                        "TB SNR [dB]": snr_range,
                        "TB BLER": new_bler
                    })

                    # Mirror subdirectory structure in output path
                    rel_path = os.path.relpath(subdir, root_dir)
                    output_subdir = os.path.join(augmented_root, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    output_file_path = os.path.join(output_subdir, file)

                    output_df.to_csv(output_file_path, index=False)

                except Exception as e:
                    print(f"Failed to process {path}: {e}")

    print("✅ All files processed successfully.")
    print(f"Total NA entries: {total_na_count}")

    return

interpolate_bler("C:/Users/Vaideeswaran/Downloads/NRV2XSL_LinkLevelDataset/Highway","Highway")
interpolate_bler("C:/Users/Vaideeswaran/Downloads/NRV2XSL_LinkLevelDataset/Urban","Urban")

# Paths
original_dir = 'C:/Users/Vaideeswaran/Downloads/NRV2XSL_LinkLevelDatasetAugmented'
results_dir = 'C:/Users/Vaideeswaran/Downloads/Results'

# Walk through the original_dir to find all .csv files
for root, dirs, files in os.walk(original_dir):
    for file in files:
        if file.endswith('.csv'):
            original_csv_path = os.path.join(root, file)

            # Read the original CSV
            df_original = pd.read_csv(original_csv_path, sep=',', keep_default_na=False)
            df_original['TB BLER'] = df_original['TB BLER'].astype(str).str.strip().str.upper()

            # Check for 'NA' presence
            na_rows = df_original['TB BLER'] == 'NA'

            if na_rows.any():
                print(f"Found {na_rows.sum()} NA entries in {file}")
                print("Unique TB BLER values with NA detected:", df_original['TB BLER'].unique())
            
                # Corresponding results CSV
                results_csv_path = os.path.join(results_dir, file)
                if not os.path.exists(results_csv_path):
                    print(f"Corresponding file not found: {results_csv_path}")
                    continue
                
                df_results = pd.read_csv(results_csv_path, sep=',')  # Changed to comma
                
                # Fill in 'NA' entries
                for idx in df_original[na_rows].index:
                    snr = df_original.loc[idx, 'TB SNR [dB]']
                    
                    # Find the matching SNR in the results file
                    match_row = df_results[df_results['SNR_dB'] == snr]
                    if not match_row.empty:
                        new_bler = match_row.iloc[0]['TB_BLER']
                        df_original.at[idx, 'TB BLER'] = new_bler
                        print(f"Updated row {idx} in {file}: SNR={snr}, BLER={new_bler}")
                    else:
                        print(f"No matching SNR={snr} found in {results_csv_path}")
                
                # Save the updated original CSV
                df_original.to_csv(original_csv_path, sep=',', index=False)
                print(f"Updated file saved: {original_csv_path}")

print("All done!")