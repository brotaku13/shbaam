#!/usr/bin/env python
#shbaam_swea.py

#Purpose:




#*******************************************************************************
#Import Python modules
#*******************************************************************************
import sys
import netCDF4
import fiona
import shapely.geometry
import shapely.prepared
import math
import rtree

def check_command_line_arg():
    ##Checks the length of arguements and if input files exist
    IS_arg = len(sys.argv)
    if IS_arg != 6:
        print('ERROR - 5 and only 5 arguments can be used')
        raise SystemExit(22) 

    for shb_file in sys.argv[2:5]:
	try:
            with open(shb_file) as file:
	        pass
	except IOError as e:
            print('ERROR - Unable to open ' + shb_file)
            raise SystemExit(22) 
    
    print('[+] Command Line Entered Properly')


def readPolygonShpFile(polyFile):
    print('Read polygon shapefile')
    polygon_file = fiona.open(polyFile, 'r')
    polygon_features=len(polygon_file)
    print(' - The number of polygone features is: ' + str(polygon_features))
    print('[+] Returned Polygon File Properly')
    return polygon_file


def createShapeFile(gld_dim_lat_length, gld_dim_lon_length, lon_dimension_array, gld_lat_length_dimension_array, polygonShapeFile, output_pnt_shp):
    shapeFile_Driver= polygonShapeFile.driver
    shapeFile_Driver_Copy = shapeFile_Driver
    
    shapeFile_crs 	= polygonShapeFile.crs
    shapeFilePoint_crs  = shapeFile_crs.copy()

	##Kept the same names, just in case
    shapeFile_schema= {'geometry':'Point',			\
			'properties':{'JS_gld_lon': 'int:4',	\
				      'JS_gld_lat': 'int:4'}}

 
    with fiona.open(output_pnt_shp, 'w', driver=shapeFile_Driver_Copy,	\
					 crs=shapeFilePoint_crs,	\
					 schema=shapeFile_schema) as pointFile:        
	for JS_gld_lon in range(gld_dim_lon_length):
	    gld_lon = gld_lon_dimension_array[JS_gld_lon]
	    if (gld_lon > 180):
		#Shifts GLD range [0:360] to [-180:180]
		gld_lon -= 180
	    for JS_gld_lat in range(gld_dim_lat_length):
		gld_lat = gld_dim_lat_length[JS_gld_lat]
		shapeFilePoint_Prepared={'JS_gld_lon':JS_gld_lon,
					'JS_gld_lat':JS_gld_lat}
		shapeFilePoint_geometry=shapely.geometry.mapping(\
			shapely.geometry.Point( (gld_lon, gld_lat) ))
		pointFile.write({
			'properties': shapeFilePoint_Prepared,
			'geometry'  : shapeFilePoint_geometry,
			})
				
    print('[+] New ShapeFile Created')


def createSpatialIndex(pointFile):
    print('Create spatial index for the bounds of each point feature')
    index = rtree.index.Index()
    
    for feature in pointFile:
	feature_id = int(feature['id'])
    	#the first argument of index.insert has to be 'int', not 'long' or 'str'
    	shape=shapely.geometry.shape(feature['geometry'])
    	index.insert(feature_id, shape.bounds)
    	#creates an index between the feature ID and the bounds of that feature

    print(' - Spatial index created')
    return index


def find_intersection(polygon, index, points):
    intersect_tot=0
    intersect_lon  =[]
    intersect_lat  =[]
    
    for area in polygon:
        shape_geo = shapely.geometry.shape(area['geometry'])
	shape_prep= shapely.prepared.prep(shape_geo)
	#a 'prepared' geometry allows for faster processing after
	for point_id in [int(x) for x in                                       \
                                  list(index.intersection(shape_geo.bounds))]:
	    shape_feature = points[point_id]
	    shape_file    = shapely.geometry(shape_feature['geometry'])
            if shape_prep.contains(shape_file):
                JS_dom_lon=shb_pnt_fea['properties']['JS_grc_lon']##CHANGE NAME !!!????
                JS_dom_lat=shb_pnt_fea['properties']['JS_grc_lat']
                intersect_lon.append(JS_dom_lon)
                intersect_lat.append(JS_dom_lat)
                intersect_tot += 1

    print(' - The number of grid cells found is: '+str(intersect_tot))
    return (intersect_tot, intersect_lon, intersect_lat)


if __name__ == '__main__':
    check_command_line_arg()

    input_gld_nc4 = sys.argv[1]	##shb_grc_ncf; Concatenated File
    input_pol_shp = sys.argv[2] ##shb_pol_ncf; Polygon File
    output_pnt_shp= sys.argv[3] ##shb_pnt_shp; Point File
    output_swe_csv= sys.argv[4] ##shb_wsa_csv; 
    output_swe_ncf= sys.argv[5] ##shb_wsa_ncf



    print('Read GLD netCDF file')
    f = netCDF4.Dataset(input_gld_nc4, 'r')

    #Get Dimension Sizes
    number_of_lon=len(f.dimensions['lon'])		##IS_grc_lon
    print(' - The number of longitudes is: '+str(number_of_lon))
    number_of_lat=len(f.dimensions['lat'])		##IS_grc_lat
    print(' - The number of latitudes is: '+str(number_of_lat))
    num_of_time_steps=len(f.dimensions['time'])		##IS_grc_time
    print(' - The number of time steps is: '+str(num_of_time_steps)

    #Value of Dimension Arrays
    gld_lon =f.variables['lon']		##ZV_grc_lon
    gld_lat =f.variables['lat']		##ZV_grc_lat
    gld_time=f.variables['time']	##ZV_grc_time

    #Get Interval Sizes
    gld_lon_interval_size =abs(gld_lon[1]-gld_lon[0])
    print(' - The interval size for longitudes is: '+str(gld_lon_interval_size))
    gld_lat_interval_size =abs(gld_lat[1]-gld_lat[0])
    print(' - The interval size for latitudes is: '+str(gld_lat_interval_size))
    if len(gld_time) > 1:
	gld_time_interval_size=abs(gld_time[1]-gld_time[0])
    else:
	gld_time_interval_size=0

    #Get Fill Values
    gld_fill = netCDF4.default.fillvals['f4']
    if 'RUNSF' in f.variables:
	gld_fill = var._FillValue
	print(' - The fill value for RUNSF is: '+str(gld_fill))
    else:
	gld_fill = None

    print('[+] Variables are set up properly')		##Can Delete



    polyShapeFile = readPolygonShpFile(input_pol_shp)	##shb_pol_lay
    createShapeFile(number_of_lat, number_of_lon, gld_lon, gld_lat, polygonShapeFile, output_pnt_shp)

    point_features=fiona.open(output_pnt_shp, 'r')		##shb_pnt_lay
    index = createSpatialIndex(point_features)
    (intersect_tot, intersect_lon, intersect_lat)=find_intersection(polyShapeFile, index, point_features)





    print('[+] Script Completed')
