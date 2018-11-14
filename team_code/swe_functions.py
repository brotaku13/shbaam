'''
Perform calculations on the grid cells: find long-term means and surface areas for each grid cell
	- total_num_cells:	the number of grid cells we are interested in, used for looping
	- grid_lats:		array of latitudes for each grid cell
	- grid_lons: 		array of longitudes (corresponding to the lats) for each grid cell
	- times: 		the total number of "times" from the time dimension of the netCDF file
	- cdf_file: 		the cdf_file itself - used to access the SWE values
	- lat_interval:		the size of the latitude interval from the netCDF file
	- lon_interval:		the size of the longitude interval from the netCDF file

Returns: Tuple containing 2 arrays: (time_averages, surface_areas)
'''
def grid_calculations(total_num_cells, grid_lats, grid_lons, times, cdf_file, lat_interval, lon_interval):
	#construct empty arrays to fill with values
	time_averages = [0] * total_num_cells
	surface_areas = [0] * total_num_cells

	#iterate through the lats and lons for each grid cell
	for grid in range(total_num_cells):
		#retrieve lat and lon
		lat = grid_lats[grid] #the latitude for the current cell
		lon = grid_lons[grid] #the longitude for the current cell

		#get the surface area for this cell and add it to the surface_areas array
		SA = 6371000 * math.radians(lat_interval) * 6371000 * math.radians(lon_interval) * math.cos(math.radians(lat)) #make a global var for 6371000
		surface_areas[grid] = SA
		
		#iterate through the grid cell at each time in the netCDf file's time dimension
		for time in range(times):
			#create a running total of SWE values in the time_averages array
			time_averages[grid] += cdf_file['SWE'][time, lat lon]
	
	#divide the values in the time_averages array by times to get the average
	time_averages = [x/times for x in time_averages]
	
	#return 2 arrays: surface areas and time_averages
	return (time_averages, surface_areas)
