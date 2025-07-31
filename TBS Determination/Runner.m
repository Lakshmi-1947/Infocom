% Runner script used to sequentially run the NRV2XSL-LinkLevelSimulator.m script
clc
close all
clear all

% Doppler shift  | Relative speed 
%      10 Hz     |      3 km/h     
%     328 Hz     |     60 km/h      
%     383 Hz     |     70 km/h      
%     656 Hz     |    120 km/h      
%     765 Hz     |    140 km/h         
%    1530 Hz     |    280 km/h      
%    2733 Hz     |    500 km/h      

% MATLAB Script to Parse CSV Files and Simulate Link Level Results

str1 = 'Highway';
str2 = 'NLOSv';
use_case = strcat(str1, str2);

fid = fopen('output.csv', 'w');
fprintf(fid, 'speed,dmrsNum,subchNum,mcsIndex,TBS\n');
fclose(fid);  % Close after writing header


ChannelModel = strcat(str1, '-', str2);

% Format: MCSindex | ModulationOrder | TargetCodeRate | SpectralEfficiency
MCS_Table = [
    0  2  120     0.2344;
    1  2  193     0.3770;
    2  2  308     0.6016;
    3  2  449     0.8770;
    4  2  602     1.1758;
    5  4  378     1.4766;
    6  4  434     1.6953;
    7  4  490     1.9141;
    8  4  553     2.1602;
    9  4  616     2.4063;
    10 4  658     2.5703;
    11 6  466     2.7305;
    12 6  517     3.0293;
    13 6  567     3.3223;
    14 6  616     3.6094;
    15 6  666     3.9023;
    16 6  719     4.2129;
    17 6  772     4.5234;
    18 6  822     4.8164;
    19 6  873     5.1152;
    20 8  683   5.3320;
    21 8  711     5.5547;
    22 8  754     5.8906;
    23 8  797     6.2266;
    24 8  841     6.5703;
    25 8  885     6.9141;
    26 8  917   7.1602;
    27 8  948     7.4063;
];

speed_array = [0, 70, 140, 280];
SCS = 30;      % 15, 30 or 60 kHz (Work with 30 kHz for now)
snr_NA = 10;


% Iterate over each file
for i = 1:length(speed_array)
    
    speed = speed_array(i);

    if speed == 0
        DopplerShift = 10;
    elseif speed == 60
        DopplerShift = 328;
    elseif speed == 70
        DopplerShift = 383;
    elseif speed == 120
        DopplerShift = 656;
    elseif speed == 140
        DopplerShift = 765;
    elseif speed == 280
        DopplerShift = 1530;
    else
        DopplerShift = NaN;
        fprintf('Unknown speed mapping: %d kmph\n', speed);
    end
    
    for subchNum = 1:5
        for dmrsNum = 2:4
            for mcsIndex = 1:28
               
                if subchNum == 1 && dmrsNum == 2
    
                    fprintf('Speed: %f, MCS Index: %d, DMRS Num: %d, SubCH Num: %d\n', speed, mcsIndex - 1, dmrsNum, subchNum);
                    tic
                    NRV2XSL_LinkLevelSimulator(speed, DopplerShift, mcsIndex - 1, SCS, dmrsNum, ChannelModel, subchNum, snr_NA) 
                    toc

                end

                if subchNum > 1

                    fprintf('Speed: %f, MCS Index: %d, DMRS Num: %d, SubCH Num: %d\n', speed, mcsIndex - 1, dmrsNum, subchNum);
                    tic
                    NRV2XSL_LinkLevelSimulator(speed, DopplerShift, mcsIndex - 1, SCS, dmrsNum, ChannelModel, subchNum, snr_NA)
                    toc
                end

            end
        end
    end
end