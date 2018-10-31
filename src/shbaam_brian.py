
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

params:
    input_netCDF4 {file} file object which is the representation of the input netCDF4 file

return:
    timestrings {list} a list of timestrings with each time representing a different month in the netCDF4 file
"""
def create_timestrings(input_netCDF4):
