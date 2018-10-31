#!/usr/bin/env python
# *******************************************************************************
# shbaam_twsa.py
# *******************************************************************************

# Purpose:
# Concatinates multiple netCDF4 files together along the time axis.
# Given multiple nc files, each of which contain consistant data in the following format:
#
# TODO: List formatting constraints

# *******************************************************************************
# Import Python modules
# *******************************************************************************
import netCDF4
from pathlib import Path
import sys
import numpy
import datetime

"""
Validates the arguments supplied. to the program. 
"""
def validate_args():
    print('Validating filepaths...')
    # check each input file for validity
    for filename in sys.argv[1: -1]:
        filepath = Path(filename)

        # Test if file is a directory and if it exists
        if not filepath.exists() or filepath.is_dir():
            print('ERROR - given file does not exist or is a directory')
            raise SystemExit(22)

        # test if file has correct extension
        if filepath.suffix != '.nc4' and filepath.suffix != '.nc':
            print(f'ERROR - {filepath.suffix} is not a valid filetype')
            print('Filetype must be either .nc or .nc4')
            raise SystemExit(22)

        # Test if file is openable
        try:
            with open(str(filepath)) as file:
                pass
        except IOError as e:
            print('ERROR - Unable to open '+ str(filepath))
            raise SystemExit(22) 

    # check output location
    output_file = Path(sys.argv[-1])

    # check if a dir was supplied
    if output_file.is_dir():
        print('ERROR - output file must be a filename, not a directory')
        raise SystemExit(22) 
    
    # test if file has correct extension
    if output_file.suffix != '.nc4' and output_file.suffix != '.nc':
        print(f'ERROR - {str(output_file)} is not a valid filetype')
        print('Filetype must be either .nc or .nc4')
        raise SystemExit(22)

    # if it passes all the tests, then continue
    print('All paths validated')
    return True

"""
We should validate the netCDF4 files to be sure they are all the same dimension sizes before attempting to merge them
Check: 
    Size of dimensions
    Names of each variable

"""
def validate_netCDF4():
    print('Validating .nc4 input variables and dimensions...')
    # should probably check if all files have the same varibles / dimensions
    pass

"""
Creates an exact copy of the input file and returns a netCDF4.Dataset of the newly created file
"""
def copy(input_filepath, output_filepath):
    print('Creating output file')
    dst = netCDF4.Dataset(output_filepath, 'w')
    with netCDF4.Dataset(input_filepath, 'r') as src:

        # copy dimensions
        print('Copying dimensions...')
        for name, dimension in src.dimensions.items():
            dst.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
            print(f'\tName: {name}\n\tLength: {len(dimension)}')

        # copy variables
        print('Initializing with data from first file')
        for name, variable in src.variables.items():
            x = dst.createVariable(name, variable.datatype, variable.dimensions)
            # copy variable attributes all at once via dictionary
            dst[name].setncatts(src[name].__dict__)
            dst[name][:] = src[name][:]
            

    print('Creation of Dimensions and Variables successful')
    return dst


"""
Takes in the variables from the input file and appends it to the output file in the "time" dimension
"""
def concatenate_file(input_file, output_file, time_slice):
    # get data in Canint Variable
    # Append data to Canint Variable in time dimension
    output_file['Canint'][time_slice + 1,:,:] = input_file['Canint'][0,:,:]
    output_file['SWE'][time_slice + 1,:,:] = input_file['SWE'][0,:,:]
    output_file.variables['time'][time_slice + 1] = time_slice + 1
    

def alter_time_dimension(output_file, input_filepaths):
    print('obtaining time series information from filenames...')
    datestrings = []
    for file in input_filepaths:
        file_name = file.split('/')[-1]
        file_date = file_name.split('.')[1]
        file_date = file_date[1:]
        year = file_date[0:4]
        month = file_date[4:]

        dt = datetime.datetime(int(year), int(month), 1)
        datestrings.append(str(dt))
    #     print(f'\t{file}\n\tCreated in: {dt}')
    
    # print('Assigning datetimes to time variable')
    nc_time = output_file.variables['time']
    # nc_time = numpy.ma.masked_array(datestrings, mask=False)
    nc_time.units = f'Months beginning at {str(datestrings[0])}'
    
    

def main():
    print('Beginning Concatenation of nc.4 files')
    print('Input Files: ')
    for p in sys.argv[1:-1]:
        print(f'\t{p}')
    print(f'Output File: \n\t{sys.argv[-1]}')
    # validate argv
    validate_args()

    # validate netCDF4 variables
    validate_netCDF4()

    # getting variables from sys.argv
    input_filepaths = sys.argv[1:-1]
    output_filepath = sys.argv[-1]

    # order output files by number
    input_filepaths = sorted(input_filepaths)

    # create output file from input file - maintaining all metadata
    print('Copying files...')
    output_netCDF4 = copy(input_filepaths[0], output_filepath)

    # run through each file and process
    try:
        for slice, file in enumerate([Path(path) for path in input_filepaths[1:]]):
            input_netCDF4 = netCDF4.Dataset(str(file), 'r')
            concatenate_file(input_netCDF4, output_netCDF4, slice)
            print(f'\tfinished {str(file)}')
            input_netCDF4.close()
        
        alter_time_dimension(output_netCDF4, input_filepaths)
        print('Copied all Files successfully')
        print('Output: ')
        print(output_netCDF4)

    except Exception as e:
        raise SystemExit('Error processing an input file.')
    finally:
        print('Closing output file and exiting program')
        output_netCDF4.close()
    


if __name__ == '__main__':
    main()


# TODO: Copy global attributes over
#       Time units