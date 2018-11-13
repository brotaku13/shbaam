import netCDF4
import datetime
import csv
import subprocess
import os

"""
Computes total terrestrial water storage anomaly timeseries. 

params:
    longitudes {list} list containing longitude values from the original input netCDF4 file
    latitudes {list} list containing latitude values from the original input netCDF4 file
    swe_average {list} list containing SWE Averages calculated over the total surface area for a particular grid cell
    surface_area {list} list containing the surface area of each grid cell
    input_netCDF4 {file} file object which is the representation of the input netCDF4 file

return: 
    {list} a list containing the total swe for a particular time (month in this case)
"""
def water_storage_timeseries(longitudes, latitudes, swe_averages, surface_areas, input_netCDF4):
    print('Compute total terrestrial water storage anomaly timeseries')

    # init timeseries
    timeseries = []

    # grab all time dimensions for the timeseries, there should be one for each month we are measuring
    times = list(input_netCDF4.dimensions['time'])
    for time in range(len(times)):
        total_swe_anomaly = 0

        # iterate through each grid cell, use swe_average since it has an average for each grid cell
        for grid_cell in range(len(swe_averages)):
            
            # init values to be used in calculations
            lon = longitudes[grid_cell]
            lat = latitudes[grid_cell]
            surface_area = surface_areas[grid_cell]
            swe_average = swe_averages[grid_cell]

            # in original code, he did something with the mask, but I don't think we have to do this? line 363-366 {?}

            # get original SWE for the grid cell at the time for this loop
            swe_total = input_netCDF4.variables['SWE'][time, lat, lon]

            # calculate the anomaly for this grid cell
            anomaly = swe_total - swe_average

            # multiply by the surface area to eliminate m^2
            anomaly *= surface_area

            # add to the running total for this period in time
            total_swe_anomaly += anomaly

            # want millimeters averaged over the entire area
            # compute mass of volume of each grid cell
            
            # add them up and divide over total area

        #append to the timeseries to get the total swe anomaly for all grid cells per time block
        timeseries.append(total_swe_anomaly)

    return timeseries

"""
Creates a series of datetime strings for each of the time dimensions in the input netCDF4 file. Will use later when creating the output CSV file
NOTE: this relies on my conc file to work accurately, because it gets access to the conc time variable and takes the date from there
params:
    input_netCDF4 {file} file object which is the representation of the input netCDF4 file

return:
    timestrings {list} a list of datetime strings with each date representing a different month in the netCDF4 file
"""
def create_timestrings(input_netCDF4):
    print('Determining datestrings...')
    #grab initial date from conc file. this uses the units from the conc file
    timestring = input_netCDF4.variables['time'].split(' ')[-1]
    origin_date = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')

    #init return array
    timestrings = [origin_date]
    
    for month_delta in range(1, len(input_netCDF4.variables['time'])):
        # adds a new month to the timestrings, passing in the previous month to add to
        timestrings.append(add_month(timestrings[month_delta - 1]))

    return [date.strftime('%m/%d/%Y') for date in timestrings]


"""
Helper function for creating datestrings. Increments the month by one. This can't be done using timedelta 
because a month is not a uniform measure. 

params:
    date {datetime} a datetime object to increment by a month

return:
    {datetime} an object which is a month ahead of the input datetime
"""
def add_month(date):
    new_year = date.year
    new_month = date.month + 1
    if new_month > 12:
        new_month = 1
        new_year += 1
    new_day = date.day
    return datetime.datetime(new_year, new_month, new_day)


"""
Creates a csv with the SWE average for each month
params:
    timestrings {list} a list of strings in MM/DD/YYYY format. One for each time dimension in the input netCDF4
    swe_sums {list} a list of swe_sums derived from the water_storage_timeseries function
    output_file {str} file string of the output file. It should have already been tested before input to this function
"""
def create_csv(timestrings, swe_sums, output_csv):
    print('Creating CSV and writing average SWE to file')
    
    # only write if we have the same number of swe sums and timestrings
    if(len(timestrings) == len(swe_sums)):

        # Open csv at the location that was given in the args
        with open(output_csv, 'wb') as csvfile:

            # create a csv writer
            csvwriter = csv.writer(csvfile, dialect='excel')

            # write the headers
            csvwriter.writerow(['Month', 'SWE Sum'])

            # loop through the results and write to the csv file
            for i in range(len(timestrings)):
                csvwriter.writerow([timestrings[i], swe_sums[i]])

    else:
        # errors out if they aren't the same length
        print('ERROR: Timestrings length is not the same as SWE sums')
        print('Timestrings length: ', len(timestrings))
        print('SWE Sums length: ', len(swe_sums))


"""
Retrieves the fillvalue from the original input netCDF4 file. If there is no fill value specified,
then it returns the default

params:
    input_netCDF4 {netCDF4.Dataseet} Dataset object from the netCDF4 library

returns:
    the fillvalue to be used when creating the netCDF4 output
"""
def get_fillvalue(input_netCDF4):
    fillvalue = netCDF4.default_fillvals['f4']
    if 'RUNSF' in input_netCDF4.variables:
        runsf = input_netCDF4.variables['RUNSF']
        if '_FillValue' in runsf.ncattrs():
            fillvalue = runsf._FillValue
            print('The fill value for RUNSF is: ', str(fillvalue))
        else:
            fillvalue = None

    return fillvalue


"""
Creates an output netCDF4 file with...

params:
    input_filepath {str} a filepath given as one of the arguments to run the script. The location of the input nc4 file
    output_filepath {str} a filepath given as one of the arguments to run the script. The location of the output nc4 file
    fillvalue {str} the fillvalue to use when creating the masked arrays. Retrieve using the get_fillvalue function defined earlier
    longitudes {list} longitudes taken from the original input nc4 file
    latitudes {list}  latitudes taken from the original input nc4 file
    swe_average {list} list containing SWE Averages calculated over the total surface area for a particular grid cell
    timeseries {list} a list containing the total swe for a particular time (month in this case)
"""
def create_output_netCDF4(input_filepath, output_filepath, fillvalue, longitudes, latitudes, swe_averages, timeseries):
    print('creating output netCDF4 file...')

    # create the output nc4 file from the filepath supplied in the args
    output_netCDF4 = netCDF4.Dataset(output_filepath, 'w'. format='NETCDF3_CLASSIC')
    input_netCDF4 = netCDF4.Dataset(input_filepath, 'r')

    # create dimensions
    create_dimensions(output_netCDF4, longitudes, latitudes)

    # create the variables then return them to use later in creating variable attributes
    variables = create_variables(output_netCDF4, fillvalue)

    # create global attributes for the nc4 file
    create_global_attributes(input_filepath, output_netCDF4)

    # create variable attributes from the original nc4 file
    copy_variable_attributes(input_netCDF4, output_netCDF4)

    # modify the CRS variable attributes (no idea why this is here)
    modify_crs_attribute(output_netCDF4, variables)

    # populate static data
    print('populating static data')
    variables['lon'][:] = input_netCDF4.variables['lon'][:]
    variables['lat'][:] = input_netCDF4.variables['lat'][:] 

    populate_dynamic_data(output_netCDF4, input_netCDF4, longitudes, latitudes, swe_averages, timeseries)

    # close files
    output_netCDF4.close()
    input_netCDF4.close()


"""
creates the dimensions for the output netCDF4 file. 

params:
    output_netCDF4 {netCDF4.Dataset} the dataset which was created
    longitudes {list} longitudes taken from the original input nc4 file
    latitudes {list}  latitudes taken from the original input nc4 file
"""
def create_dimensions(output_netCDF4, longitudes, latitudes):
    print('creating dimensions...')
    time = output_netCDF4.createDimension('time', None)
    lat = output_netCDF4.createDimension('lat', len(latitudes))
    lon = output_netCDF4.createDimension('lon', len(longitudes))
    nv = output_netCDF4.createDimension('nv', 2)  # no idea why this is here


"""
Creates the variables for the output nc4 file
params:
    output_netCDF4 {netCDF4.Dataset} the dataset which was created
    fillvalue {str} the fillvalue to be used in the swe variable

returns:
    {dict} the new variables objects of the output dataset in {'name': variable} format
"""
def create_variables(output_netCDF4, fillvalue):
    print('creating variables')
    time = output_netCDF4.createVariable('time', 'i4', ('time',))
    time_bands = output_netCDF4.createVariable('time_bands', 'i4', ('time', 'nv'))
    lat = output_netCDF4.createVariable('lat', 'f4', ('lat',))
    lon = output_netCDF4.createVariable('lon', 'f4', ('lon',))
    swe = output_netCDF4.createVariable('swe', 'f4', ('time', 'lat', 'lon'), fill_value=fillvalue)

    # not sure what crs is
    crs = output_netCDF4.createVariable('crs', 'i4')

    return {
        'time': time,
        'time_bands': time_bands,
        'lat': lat,
        'lon': lon,
        'swe': swe,
        'crs': crs
    }


"""
Creates the global variables for the output nc4 file
params:
    output_netCDF4 {netCDF4.Dataset} the dataset which was created
"""
def create_global_attributes(input_filepath, output_netCDF4):
    # Get current time without microseconds
    dt = datetime.datetime.utcnow()
    dt = dt.replace(microsecond=0)

    # grab the current version of shbaam
    version = subprocess.Popen('bash ../version.sh', stdout=subprocess.PIPE, shell=True).communicate()
    version = version[0].rstrip()

    # create global attributes
    output_netCDF4.Conventions = 'CF-1.6'
    output_netCDF4.title = ''
    output_netCDF4.institution = ''
    output_netCDF4.source = 'SHBAAM: ' + version + 'GRACE: ' + os.path.basename(input_filepath)
    output_netCDF4.history = 'date created: ' + dt.isoformat() + '+00:00'
    output_netCDF4.references = 'https://github.com/c-h-david/shbaam/'
    output_netCDF4.comment = ''
    output_netCDF4.featureType = 'timeSeries'


"""
Copies the attributes from the input netCDF4 file provided in the program args over to
the newly created output file. 

params: 
    input_filepath {str} the filepath to the input nc4 file
    destination {netCDF4.Dataset} the dataset which was created
"""
def copy_variable_attributes(source, destination):

    print('Copying variable attributes...')

    # copy over every variable attribute in the source attributes
    for name, variable in source.variables.items():
        var = destination.variables[name]
        destination[name].setncatts(source[name].__dict__)


    # this should be revised to only grab feasable attributes


"""
These are for the WGS84 spheroid

params:
    output_netCDF4 {netCDF4.Dataset} the dataset which was created
    output_variables {dict} the variables objects of the output dataset in {'name': variable} format
"""
def modify_crs_attribute(output_netCDF4, output_variables):
    output_variables['swe'].grid_mappings = 'crs'
    output_variables['crs'].grid_mapping_name = 'latitude_longitude'
    output_variables['crs'].semi_major_axis = '6378137'
    output_variables['crs'].inverse_flattening = '298.257223563' 


"""
populates the output file with the relavent data
"""
def populate_dynamic_data(output_netCDF4, input_netCDF4, longitudes, latitudes, swe_averages, timeseries):
    print('populate dynamic data...')

    for grid_cell in range(len(swe_averages)):
        lon = longitudes[grid_cell]
        lat = latitudes[grid_cell]
        swe_average = swe_averages[grid_cell]
        
        for time in range(len(timeseries)):
            output_netCDF4.variables['swe'][time, lat, lon] = input_netCDF4.variables['SWE'][time, lat, lon] - swe_average

    # why do we do this?
    output_netCDF4.variables['time'][:] = output_netCDF4.variables['time'][:] 