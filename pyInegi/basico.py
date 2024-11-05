from shapely import *
import folium
import numpy as np
import shapely as shpy
import geopandas as gpd
import os

def punto(x,y):
	return Point(x,y)

def plot(gdf):
	m = gdf.explore(column="id", cmap="Set1", name="id", legend=True, popup=True)
	folium.TileLayer('OpenStreetMap').add_to(m)
	folium.LayerControl().add_to(m)
	m.show_in_browser()


def dist2pnts(x1, y1, x2, y2):
	return ((x2-x1)**2+(y2-y1)**2)**0.5
def importarSHP(shp):
	import fiona
	with fiona.open(shp) as shapefile:
		for record in shapefile:
			print(record)
def shp2DF(shp,cuantos=None,campos=None):
	return gpd.read_file(shp,rows=cuantos,columns=campos)
def importFeat(gdb, feat, campos=None):
	return gpd.read_file(gdb,layer=feat,columns=campos)
def capa2Excel(gdb,feat,nom,campos=None):
	tabla = gpd.read_file(gdb,layer=feat,columns=campos)
	return tabla.to_excel(f"{nom}.xlsx")
def capa2Excel(shp,nom,campos=None):
	tabla = gpd.read_file(shp,columns=campos)
	return tabla.to_excel(f"{nom}.xlsx")
def pol2Linea(pol):
	geo=list(pol.__geo_interface__['coordinates'][0])
	return [shpy.LineString([shpy.Point(*list(geo[i-1])),shpy.Point(*list(geo[i]))]) for i in range(1,len(geo))]


def sepa(c="*-*-"):
  print("%s" * 20  % tuple([c for i in range(20)]))

def fechaHora():
  import datetime as dt
  t = dt.datetime.today()
  return str(t)[:-7].replace(" ","-").replace(":","")

def imp(text):
  import datetime as dt
  t = dt.datetime.today()
  print("|%s|  %s" % (str(t)[5:-5],str(text)))

def colores(v):
  return "red" if v==True else "gray"

data = {'dist':120.0,'EPSILON':0.001000,'APROX':0.020000}