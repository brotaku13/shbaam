import netCDF4
import datetime
import csv

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

input:
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

