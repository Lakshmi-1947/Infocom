import os
import pandas as pd

def find_files_with_bler_below_threshold(base_path, snr_input, bler_threshold):
    matching_files = []
    
    # Check if the base path exists
    if not os.path.exists(base_path):
        print(f"Base path does not exist: {base_path}")
        return matching_files

    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)
                    
                    # Check if the required columns exist
                    if 'TB SNR [dB]' in df.columns and 'TB BLER' in df.columns:
                        # Filter rows for the given SNR
                        snr_match = df[df['TB SNR [dB]'] == snr_input]
                        
                        if not snr_match.empty:
                            # Check if any BLER in these rows is below the threshold
                            if (snr_match['TB BLER'] < bler_threshold).any():
                                matching_files.append(file_path)
                    else:
                        print(f"Skipping file (missing columns): {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return matching_files

bler_threshold = 0.1  # Example BLER threshold
if bler_threshold == 0.1:
    reliability = "Low"
elif bler_threshold == 0.01:
    reliability = "High"

scenario = "Urban"  # Example scenario
speed = "120kmph"  # Example speed
channel_condition = "NLOSv"  # Example channel condition

if scenario == "Urban":
    snr_range = [i for i in range(-13, 46, 1)]  # SNR range for Urban scenario
else:
    snr_range = [i for i in range(-13, 51, 1)]

#########################################################################################################################################################################

base_path = "C:/Users/Vaideeswaran/Documents/ACS Project/Monte Carlo Dataset/NRV2XSL_LinkLevelDatasetAugmented/" + scenario + "/" + channel_condition + "/" + speed
TBS_data_path = "C:/Users/Vaideeswaran/Documents/ACS Project/TBS Determination/output.csv"

MCS_LuT = {
    (2, 120): 0,
    (2, 193): 1,
    (2, 308): 2,
    (2, 449): 3,
    (2, 602): 4,
    (4, 378): 5,
    (4, 434): 6,
    (4, 490): 7,
    (4, 553): 8,
    (4, 616): 9,
    (4, 658): 10,
    (6, 466): 11,
    (6, 517): 12,
    (6, 567): 13,
    (6, 616): 14,
    (6, 666): 15,
    (6, 719): 16,
    (6, 772): 17,
    (6, 822): 18,
    (6, 873): 19,
    (8, 683): 20,
    (8, 711): 21,
    (8, 754): 22,
    (8, 797): 23,
    (8, 841): 24,
    (8, 885): 25,
    (8, 917): 26,
    (8, 948): 27,
}

def recommender(base_path, snr_range, bler_threshold, MCS_LuT, TBS_data_path, reliability):
    recommendation_dict = {}

    for snr_input in snr_range:

        result_files = find_files_with_bler_below_threshold(base_path, snr_input, bler_threshold)

        if len(result_files) == 0:
            recommendation_dict[snr_input] = "None"
            continue

        TBS_dict = {}

        for file in result_files:
            file_path = file.replace("\\", "/")
            path_parts = file_path.split("/")

            # Extract parameters
            num_subchannels = int([part for part in path_parts if "Subch" in part][0].replace("Subch", ""))
            num_dmrs = int([part for part in path_parts if "DMRS" in part][0].replace("DMRS", ""))

            filename = os.path.basename(file_path)

            if "QPSK" in filename:
                modulation_order = 2
            elif "16QAM" in filename:
                modulation_order = 4
            elif "64QAM" in filename:
                modulation_order = 6
            elif "256QAM" in filename:
                modulation_order = 8
            else:
                raise ValueError(f"Unknown modulation in filename: {filename}")

            mcs = int(filename.split("-")[-1].replace(".csv", ""))
            mcs_index = MCS_LuT.get((modulation_order, mcs))

            df = pd.read_csv(TBS_data_path)

            row = df[
                (df['dmrsNum'] == num_dmrs) &
                (df['subchNum'] == num_subchannels) &
                (df['mcsIndex'] == mcs_index)
            ]

            tbs_value = row['TBS'].values[0]
            TBS_dict[(num_subchannels, num_dmrs, mcs_index)] = tbs_value

        max_TBS = max(TBS_dict.values())
        max_keys = [k for k, v in TBS_dict.items() if v == max_TBS]

        max_mcs_index = max(k[2] for k in max_keys)
        mcs_tied_keys = [k for k in max_keys if k[2] == max_mcs_index]

        if len(mcs_tied_keys) == 1:
            recommendation_dict[snr_input] = mcs_tied_keys[0]
        else:
                # Apply further tie-breaking:
                # First, check if subchannel count is identical, prefer lower DMRS
            subch_values = set(k[0] for k in mcs_tied_keys)
            dmrs_values = set(k[1] for k in mcs_tied_keys)

            if len(subch_values) == 1:
                # All have same subchannels → prefer lower DMRS
                best = min(mcs_tied_keys, key=lambda x: x[1])  # x[1] is DMRS
            elif len(dmrs_values) == 1:
                # All have same DMRS → prefer higher subchannels
                best = max(mcs_tied_keys, key=lambda x: x[0])  # x[0] is subchannels
            else:
                print(f"Full tie at SNR {snr_input}: {mcs_tied_keys}")
                # best = mcs_tied_keys[0]

            recommendation_dict[snr_input] = best
    
    return recommendation_dict

# Test the recommender function

recommendation_dict = recommender(base_path, snr_range, bler_threshold, MCS_LuT, TBS_data_path, reliability)

# Save the recommendation list to a CSV file
output_df = pd.DataFrame(recommendation_dict.items(), columns=['SNR', 'Recommendation'])
output_df.to_csv(f'C:/Users/Vaideeswaran/Documents/ACS Project/Recommendations/recommendation_dict_{scenario}_{channel_condition}_{speed}_{reliability}.csv', index=False)
        