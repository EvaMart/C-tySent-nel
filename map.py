import folium
coordinates = [41.390205, 2.154007]

folium_map = folium.Map(location=coordinates, zoom_start=12, tiles = "openstreetmap")
folium_map.add_child(folium.LatLngPopup())

folium_map.save('maps/maps_event.html')
