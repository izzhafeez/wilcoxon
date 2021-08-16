import requests
import pandas as pd
import geopandas as gpd
import json
from . import sheets
from .utils import *
import itertools
import shapely
import contextily as ctx
from tqdm import tqdm
import matplotlib.pyplot as plt
import fiona


def getMRT():
	"""
	PURPOSE (NO LONGER WORKS FULLY)

	I made this code to extract all the kinds of data you'd want to know about MRT and LRT stations.
	More specific information will be given in comments below but as of now, here is the link: https://docs.google.com/spreadsheets/d/e/2PACX-1vQIXKejfbHe2FuPKp0qvdS6OfLDceHGO2WvxGgJtyuoD6HyAmd9Qxj8NZsJA4JItvPcqRKyMJUdDVF-/pub?gid=1134364680&single=true&output=pdf
	Do note that this is not the full version of the dataset, as I wanted to only keep the essentials in there.

	Download data for train station exits: TrainStationExit_Jan2020/TrainStationExit06032020.shp
	Download data for train stations: TrainStation_Jan2020/MRTLRTStnPtt.shp
	Download data for OriginDestinationTrain: origin_destination_train_202103.csv
	"""
	path_to_TrainStationExits = ""
	path_to_TrainStations = ""
	path_to_OriginDestinationTrain = ""


	print("Extracting Wikipedia links of MRT and LRT stations.")
	"""
	PURPOSE

	DOES NOT WORK NOW BECAUSE WIKIPEDIA CHANGED THE FORMAT OF THE PAGE.
	But what this section does is extract the links to all the Wikipedia pages of the respective MRT and LRT stations.
	Changi Airport, Expo, Tanah Merah and Damai LRT were added manually because they were not found anywhere within the landing page.
	"""
	stations = website("https://en.wikipedia.org/wiki/List_of_Singapore_MRT_stations")
	stations.getTables()
	stationLinksM = stations.tables[1]["Links"].apply(lambda x: x.split("\n")[0]).tolist()
	stationLinksM = [x for x in stationLinksM if ("a"+x)[-1] == "n"]
	stationLinksM.extend(["https://en.wikipedia.org/wiki/Changi_Airport_MRT_station",
						 "https://en.wikipedia.org/wiki/Expo_MRT_station",
						 "https://en.wikipedia.org/wiki/Tanah_Merah_MRT_station"])

	stations = website("https://en.wikipedia.org/wiki/List_of_Singapore_LRT_stations")
	stations.getTables()
	stationLinksL = stations.tables[0]["Links"].apply(lambda x: x.split("\n")[0]).tolist()
	stationLinksL = [x for x in stationLinksL if ("a"+x)[-1] == "n"]
	stationLinksL.extend(["https://en.wikipedia.org/wiki/Damai_LRT_station_(Singapore)"])

	stationLinks = list(set(stationLinksM + stationLinksL))


	print("Extracting data from Wikipedia pages.")
	"""
	PURPOSE

	Each page within the links has many key information scattered in various places.
	It was a challenge to make sure all the information from every page was captured, even if the data is inconsistently placed.
	The whole section below is to extract:
		Station Labels (NS26, EW14)
		Station Name (Raffles Place)
		Chinese Translation (莱佛士坊)
		Address (5 Raffles Place)
		Postal Code (048618)
		Latitude (Derived from 1°17′1.97″)
		Longitude (Derived from 103°51′5.52″)
	"""
	mrt = []

	for link in tqdm(stationLinks):
		site = website(link)
		try:
			stationName = site.html("title")[0].string.split(" MRT")[0]
		except Exception as e:
			print("stationName gave the error: " + str(e) + "\n" + link)
			stationName = None
		
		try:
			stationDetails = list(site.html.find(class_="fn org").stripped_strings)
			chineseIndex = 0
			for detail in stationDetails:
				if re.compile('[\u4e00-\u9fff]+').search(detail):
					chineseIndex = stationDetails.index(detail)
			stationLabels = ", ".join(stationDetails[:chineseIndex-1])
			stationChinese = stationDetails[chineseIndex]
		except Exception as e:
			print("stationLabels gave the error: " + str(e) + "\n" + link)
			stationLabels = None
			stationChinese = None
		
		try:
			lat = convertCoords(*re.findall("[0-9.]+", site.html(class_="latitude")[0].text))
			long = convertCoords(*re.findall("[0-9.]+", site.html(class_="longitude")[0].text))
		except Exception as e:
			print("latlong gave the error: " + str(e) + "\n" + link)
			lat = None
			long = None

		try:
			fullAddress = list(site.html(class_="infobox-data")[0].strings)
			address = fullAddress[0]
			postcode = re.findall(r"\d{6}", fullAddress[1])[0]
		except Exception as e:
			print("address gave the error: " + str(e) + "\n" + link)
			address = None
			postcode = None
		mrt.append({"Label": stationLabels, "Name": stationName, "Chinese": stationChinese, "Address": address, "Postcode": postcode, "Lat": lat, "Long": long, "Link": link})


	print("Mapping station names to their abbreviations.")
	"""
	PURPOSE

	The abbreviations to the MRT and LRT stations are captured in the site listed below.
	So it was a matter of extracting them and mapping them to the existing data.
	"""
	site = website("https://en.wikipedia.org/wiki/List_of_Singapore_MRT_stations")
	abbrMapping = {}
	for t in site.html("td",text=re.compile("^[A-Z]{3}$")):
	    if t.text != "TBA":
	        abbrMapping[t.find_previous("a",href=True).text.strip()] = t.text

	def tryAbb(x):
	    try: return abbrMapping[x]
	    except: return ""

	mrt["Abbreviation"] = mrt.Name.apply(tryAbb)

	mrt = pd.DataFrame(mrt)


	print("Finding coordinates of exits of MRT and LRT stations.")
	"""
	PURPOSE

	As of this point, the information gathered is more than enough for my purposes.
	However, just to finish things off, the following steps take things a whole step further.
	With the help of a couple of datasets from LTA Data Mall, we can now know:
		The locations of the exits to the existing MRT and LRT stations.
		The number of passengers to and from stations.

	I also did a mapping from the labels of the staitons (NS26, EW14) into their respective colors.
	"""
	exits = gpd.read_file(path_to_TrainStationExits)
	exits["STN_NAME"] = exits["STN_NAME"].str.replace(" .RT STATION","").str.replace(" STATION","")
	exits = exits[["STN_NAME","EXIT_CODE","geometry"]]
	exits.columns = ["Name","Exit","geometry"]

	stations = gpd.read_file(path_to_TrainStations)
	stations["geometry"] = stations.geometry.to_crs(epsg=4326)
	stations["STN_NAME"] = stations["STN_NAME"].str.replace(" .RT STATION","").str.replace(" STATION","")
	stations = stations[["STN_NAME","STN_NO","geometry"]]
	stations.columns = ["Name","Exit","geometry"]

	mrtFull = mrt.copy()
	mrtFull["Name"] = mrtFull.Name.str.upper().str.replace(" .RT STATION.*$","")
	mrtFull = pd.concat([mrtFull.merge(stations, how="left"),
	                     mrtFull.merge(exits, how="left")])

	mrtFull["Exit"] = mrtFull[["Exit","Label"]].apply(lambda x: x[1] if pd.isna(x[0]) else x[0], axis=1)
	mrtFull = gpd.GeoDataFrame(mrtFull, geometry="geometry")
	mrtFull["Labels"] = mrtFull.Label.copy()
	mrtFull["Label"] = mrtFull["Exit"]
	mrtFull = mrtFull.drop("Exit",axis=1)

	mrtFull = mrtFull[["Label","Name","Chinese","Address","Postcode","Lat","Long","Labels","geometry","Link"]]
	mrtFull["Name"] = mrtFull.Name.str.replace(" LRT.*?$","")
	mrtFull["Long"] = mrtFull[["geometry","Long"]].apply(lambda x: x[1] if pd.isna(x[0]) else x[0].x, axis=1)
	mrtFull["Lat"] = mrtFull[["geometry","Lat"]].apply(lambda x: x[1] if pd.isna(x[0]) else x[0].y, axis=1)

	mrtFull["Label"] = mrtFull.Label.str.split("[,/]")
	mrtFull = gpd.GeoDataFrame(pd.DataFrame(mrtFull).explode("Label"))
	mrtFull["Label"] = mrtFull.Label.str.strip()
	mrtFull["line"] = mrtFull.Label.str.extract(r"(\D+)").fillna(0)
	mrtFull = mrtFull[mrtFull.line != 0]

	passengers = pd.read_csv(path_to_OriginDestinationTrain)
	passengers.ORIGIN_PT_CODE = passengers.ORIGIN_PT_CODE.str.split("/")
	passengers.DESTINATION_PT_CODE = passengers.DESTINATION_PT_CODE.str.split("/")
	passengers = passengers.explode("ORIGIN_PT_CODE")
	passengers = passengers.explode("DESTINATION_PT_CODE")
	passengers.ORIGIN_PT_CODE = passengers.ORIGIN_PT_CODE.str.strip()
	passengers.DESTINATION_PT_CODE = passengers.DESTINATION_PT_CODE.str.strip()

	mrtFull = mrtFull.merge(pd.DataFrame(passengers.groupby("ORIGIN_PT_CODE").pipe(lambda x: x.TOTAL_TRIPS.sum())),
	                        left_on="Label", right_on="ORIGIN_PT_CODE", how="left")
	mrtFull = mrtFull.merge(pd.DataFrame(passengers.groupby("DESTINATION_PT_CODE").pipe(lambda x: x.TOTAL_TRIPS.sum())),
	                        left_on="Label", right_on="DESTINATION_PT_CODE", how="left")
	mrtFull = mrtFull.rename(columns={"TOTAL_TRIPS_x":"Origin", "TOTAL_TRIPS_y":"Destination"})

	colorMap = {"EW":"#009645",
	           "CG":"#009645",
	           "NS":"#D42E12",
	           "NE":"#9900AA",
	           "CC":"#FA9E0D",
	           "CE":"#FA9E0D",
	           "DT":"#005EC4",
	           "TE":"#9D5B25",
	           "JE":"#0099AA",
	           "JS":"#0099AA",
	           "JW":"#0099AA",
	           "CR":"#97C616",
	           "CP":"#97C616",
	           "PE":"#748477",
	           "PW":"#748477",
	           "PT":"#748477",
	           "ST":"#748477",
	           "SE":"#748477",
	           "SW":"#748477",
	           "BP":"#748477",
	           "RT":"#86CEEB"}

	mrtFull["color"] = mrtFull.Label.apply(lambda x: colorMap[x[:2]] if x[:2] in colorMap.keys() else None)
	mrtFull["number"] = mrtFull.Label.str.extract(r"(\d+)").fillna("1000")
	mrtFull["number"] = mrtFull.number.apply(int)
	mrtFull["Type"] = mrtFull.line.apply(lambda x: "Station" if len(x) > 1 else "Exit")

	mrtFull = mrtFull[['Label', 'Name', 'Chinese', 'Address', 'Postcode', 'Lat', 'Long', 
	                   'Labels', 'Type', 'Origin', 'Destination', 'geometry', 'color', 'line', 'number', 'Link']]
		
	return(mrt, mrtFull)


def getBus(accountKey):
	"""
	PURPOSE

	I made this code to extract all the kinds of data you'd want to know about bus services and stations:
		Service No
		Operator
		BusStopCode
		Distance to next stop
		Road Name
		Description
		Latitude
		Longitude
		Altitude
		Passenger Inflow
		Passenger Outflow

	Here is the link: https://docs.google.com/spreadsheets/d/e/2PACX-1vQIXKejfbHe2FuPKp0qvdS6OfLDceHGO2WvxGgJtyuoD6HyAmd9Qxj8NZsJA4JItvPcqRKyMJUdDVF-/pub?gid=1421914910&single=true&output=pdf

	Download data for OriginDestinationBus: origin_destination_train_202103.csv
	"""
	path_to_OriginDestinationBus = ""


	busRoutes = []
	starting = 0
	while True:
		try:
			headers = {'AccountKey':accountKey}
			results = requests.get('http://datamall2.mytransport.sg/ltaodataservice/BusRoutes?$skip=' + str(starting),headers=headers).text
			results = json.loads(results)
			if len(results['value']) == 0:
				break
			busRoutes.extend(results['value'])
			starting += 500
		except: break

	busStops = []
	starting = 0
	while True:
		try:
			headers = {'AccountKey':accountKey}
			results = requests.get('http://datamall2.mytransport.sg/ltaodataservice/BusStops?$skip=' + str(starting),headers=headers).text
			results = json.loads(results)
			if len(results['value']) == 0:
				break
			busStops.extend(results['value'])
			starting += 500
		except: break

	bus = pd.DataFrame(busRoutes).merge(pd.DataFrame(busStops))

	passengers = pd.read_csv(path_to_OriginDestinationBus)
	tapIn = passengers.groupby("PT_CODE").pipe(lambda x: x.TOTAL_TAP_IN_VOLUME.sum())
	tapOut = passengers.groupby("PT_CODE").pipe(lambda x: x.TOTAL_TAP_OUT_VOLUME.sum())
	passengers = pd.DataFrame([tapIn, tapOut]).T
	passengers = passengers.reset_index()
	passengers.columns = ["BusStopCode","In","Out"]

	return bus.merge(passengers)

def getRoads():
	"""
	PURPOSE

	I made this code to extract combine road data with planning area data.
	It is used to find roads within any particular planning area.

	Download data for road network: master-plan-2019-road-name-layer/road-network.kml
	Download data for planning areas: subzone-census-2010/Subzone_Census2010.kml
	"""
	path_to_RoadNetwork = ""
	path_to_PlanningAreas = ""


	gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
	roads = gpd.read_file(path_to_RoadNetwork, driver='KML')
	roads["Name"] = roads.Description.str.extract("<td>(.*?)</td>")
	roads["Type"] = roads.Description.str.extract("RD_TYP_CD</th>.*?<td>(.*?)</td>")
	roads = roads.drop("Description",axis=1)

	planning = gpd.read_file(path_to_PlanningAreas, driver='KML')
	planning["SubzoneCode"] = planning.Description.str.extract("Subzone Code.*?<td>(.*?)</td>")
	planning["Planning"] = planning.Description.str.extract("Planning Area Name.*?<td>(.*?)</td>")
	planning["PlanningCode"] = planning.Description.str.extract("Planning Area Code.*?<td>(.*?)</td>")
	planning["Region"] = planning.Description.str.extract("Region Name.*?<td>(.*?)</td>")
	planning["RegionCode"] = planning.Description.str.extract("Region Code.*?<td>(.*?)</td>")
	planning = planning.rename(columns={"Name":"Subzone"})
	planning = planning.drop("Description",axis=1)
	planning = planning[['Region', 'RegionCode', 'Planning', 'PlanningCode', 'Subzone', 'SubzoneCode', 'geometry']]

	roadsm = roads.values.tolist()
	planningm = planning.values.tolist()

	roads = []
	for road, line, rType in tqdm(roadsm):
	    appeared = False
	    for *details, shape in planningm:
	        if line.within(shape) or line.intersects(shape):
	            roads.append((road, rType, line) + tuple(details))
	            appeared = True
	    if not appeared:
	        roads.append((road, rType, line) + ("",)*6)

	roads = gpd.GeoDataFrame(roads)
	roads.columns = ["Road", "Type", "geometry", "Region", "RegionCode", "Planning", "PlanningCode", "Subzone", "SubzoneCode"]

	"""
	PURPOSE

	Visualisation of roads in Singapore.
	"""
	ax = roads[roads.Region != ""].plot(figsize=(15,15), column="Subzone")
	ctx.add_basemap(ax=ax, zoom=13, crs="EPSG:4326")


def generateElevationMap():
	"""
	PURPOSE

	To estimate the altitude of a particular location, you need to preprocess the contour lines first.
	That's what this code is for.
	Be sure to save the output of this code as a variable, as it will be used for the actual altitude code.

	Download national_map_line data: national-map-line/national-map-line-geojson.geojson
	"""

	path_to_NationalMapLine = ""


	elevation = gpd.read_file(path_to_NationalMapLine)
	elevation["Location"] = elevation.Description.str.extract("<td>(.*?)</td>")

	elevation = elevation[elevation.Location.str.contains(r"^\d+$")]
	L = []
	for geometry in elevation.geometry.tolist():
	    try:
	        L.append(shapely.geometry.Polygon([(float(i[0]), float(i[1])) for i in re.findall(r"(\d+\.\d+)\s(\d+\.\d+)", str(geometry))]))
	    except:
	        L.append("")
	elevation["polygon"] = L
	elevation = elevation[elevation.polygon != ""]

	multipolygons = []
	for location in elevation.Location.unique():
	    multipolygons.append({"alt": int(location), "geometry":shapely.geometry.MultiPolygon(elevation[elevation.Location == location].polygon.tolist())})
	    
	return gpd.GeoDataFrame(multipolygons)


def alt(coords, elevationMap):
	"""
	PURPOSE

	To find the altitude (or elevation) of a particular point in Singapore.
	The way this code works is just finding the distance between the point and the two closest contour lines to it.
	Then, by some formula (can see below), an estimation is made.

	PARAMETERS

	elevationMap: obtained when running the previous code, generateElevationMap()
	coords [tuple of longitude and latitude]
	"""
    closestDistances = {x: 1000 for x in elevationMap.alt.unique()}
    maxalt = 0

    for polygon, alt in elevationMap[["polygon","Location"]].values.tolist():
        point = coords
        distance = polygon.exterior.distance(point)
        closestDistances[int(alt)] = min(closestDistances[int(alt)], distance)
        if point.within(polygon) and maxalt < int(alt):
            maxalt = int(alt)

    return ((maxalt + 20) * closestDistances[maxalt] + (maxalt) * closestDistances[maxalt + 20]) / (closestDistances[maxalt] + closestDistances[maxalt + 20])



def getParkingLots(accountKey):
	"""
	PURPOSE

	Gets the number of Parking lots for particular locations.
	"""
	parking = []
	starting = 0
	while True:
		try:
			headers = {'AccountKey':accountKey}
			results = requests.get('http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip=' + str(starting),headers=headers).text
			results = json.loads(results)
			if len(results['value']) == 0:
				break
			parking.extend(results['value'])
			starting += 500
		except: break

	return pd.DataFrame(parking)


