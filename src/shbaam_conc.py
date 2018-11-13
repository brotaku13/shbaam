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
import os
import glob
import sys
import numpy
import datetime

"""
Validates argumnets supplied
"""
def validate_args(args):
    print('---------')
    print(args)
    for file in glob.glob(args[0]):
        if not os.path.isfile(args[0]):
            raise FileNotFoundError('The file ' + file + ' is not valid')

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
            print('\tName: {}\n\tLength: {}'.format(name, len(dimension)))

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
    
    
    # print('Assigning datetimes to time variable')
    nc_time = output_file.variables['time']
    # nc_time = numpy.ma.masked_array(datestrings, mask=False)
    nc_time.units = 'Months beginning at ' + str(datestrings[0])
    
    

def main():
    print('Beginning Concatenation of nc.4 files')
    print('Input Files: ')
    for p in sys.argv[1:-1]:
        print('\t' + p)
    print('Output File: ' + str(sys.argv[-1]))
    # validate argv
    validate_args(sys.argv[1:])

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
        time_slice = 0
        for file in input_filepaths[1:]:
            input_netCDF4 = netCDF4.Dataset(str(file), 'r')
            concatenate_file(input_netCDF4, output_netCDF4, time_slice)
            print('\tFinished '+ str(file))
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