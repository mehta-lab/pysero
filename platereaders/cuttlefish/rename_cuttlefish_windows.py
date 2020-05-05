
#%% imports
import pandas as pd
import skimage
from skimage import util
from skimage import io
from skimage import transform
from skimage.util import img_as_ubyte
import os

DATA_PATH="C:\\Users\\gt8ma\\OneDrive\\Documents\\2019-2020 School Year\\BioHub\\2020-05-01-17-29-54-COVID_May1_JBassay_images"
filemap="C:\\Users\\gt8ma\\OneDrive\\Documents\\2019-2020 School Year\\BioHub\\2020-05-01-17-29-54-COVID_May1_JBassay_images\\cuttlefish_wellToFile_windows.xlsx"
ROTATION_ANGLE = -5.15



def main():
    #%% read the map between filenames.
    filemap_df=pd.read_excel(filemap, header=0) # df is dataframe
    # Linearlize the table
    filemap_df = filemap_df.melt(id_vars=['rows'])
    filemap_df=filemap_df.rename(columns={'variable':'columns','value':'path'})
    filemap_df['well']=filemap_df['rows']+filemap_df['columns'].astype(str)+".png"
    # print(filemap_df)
    # Above results in a 96-row table with 'well' column
    for index in range(len(filemap_df)):
        # This loops through the files.
        img2 = rotate(filemap_df['path'][index], filemap_df['columns'][index]) # pass in the columns and the filename
        # Change the numpy array from float to uint8 so that we can save
        img2 = img_as_ubyte(img2)
        # Save the file back to the folder with a new name
        io.imsave(filemap_df['well'][index], img2)


def rotate(file, column):
    """
    This function rotates the file by a designated amount.
    :param: pass in the file name
    :return: The image data
    """
    if column < 11:
        # read in files for columns 1-10
        filename = os.path.join(DATA_PATH, file)
        img = io.imread(filename)
        # Rotate image
        img = skimage.transform.rotate(img, ROTATION_ANGLE)
    else:
        # read in files for columns 11 and 12
        filename = os.path.join(DATA_PATH, file)
        img = io.imread(filename)
        # Rotate image
        img = skimage.transform.rotate(img, ROTATION_ANGLE - 180)
    return img

        # Read as numpy array.

        # Rotate by correct angle. Rotation angles will be different for columns 1-10, and 11:12
        # if filemap_df['columns']<=10:
        #     print('one angle')
        # else:
        #     print('another angle')

    # Write as a png file in datadir.

# This provided line is required at the end of a Python file
# to call the main() function.
if __name__ == '__main__':
    main()
