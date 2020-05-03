#%% imports
import pandas as pd
datadir='/Volumes/GoogleDrive/My Drive/ELISAarrayReader/images_cuttlefish/2020-05-01-17-29-54-COVID_May1_JBassay_images'
filemap='/Volumes/GoogleDrive/My Drive/ELISAarrayReader/images_cuttlefish/cuttlefish_wellToFile.xlsx'

#%% read the map between filenames.
filemap_df=pd.read_excel(filemap,header=0) # df is dataframe
# Linearlize the table
filemap_df=filemap_df.melt(id_vars='rows')
filemap_df=filemap_df.rename(columns={'variable':'columns','value':'path'})
filemap_df['well']=filemap_df['rows']+filemap_df['columns'].astype(str)
# Above results in a 96-row table with 'well' column
for idx in range(len(filemap_df)):
    # This is how you can index into linear table to read input path and output path.

    print(filemap_df['path'][idx])
    print('->'+filemap_df['well'][idx])

    # Read as numpy array.

    # Rotate by correct angle. Rotation angles will be different for columns 1-10, and 11:12
    if filemap_df['columns']<=10:
        print('one angle')
    else:
        print('another angle')

# Write as a png file in datadir.
