import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'react-leaflet';
import { convex } from '@turf/convex';
import { points } from '@turf/helpers';
import { useDashboardData } from '../hooks/useDashboardData';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet's default icon path issues in Vite
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;
const RiskMapView = () => {
    const { devices } = useDashboardData();

    // 1. Filter only devices with VALID coordinates
    const validDevices = devices?.filter(d =>
        d.sensorData?.lat !== undefined &&
        d.sensorData?.lon !== undefined
    ) || [];

    const areaPolygon = useMemo(() => {
        if (validDevices.length < 3) return null;
        // ... existing polygon logic using validDevices ...
        const turfPoints = points(validDevices.map(d => [d.sensorData.lon, d.sensorData.lat]));
        const hull = convex(turfPoints);
        if (!hull) return null;
        return hull.geometry.coordinates[0].map(coord => [coord[1], coord[0]]);
    }, [validDevices]);

    // 2. Safety Check: If no devices have GPS, hide the map
    if (validDevices.length === 0) return null;

    // Center on the first VALID device
    const center = [validDevices[0].sensorData.lat, validDevices[0].sensorData.lon];

    return (
        <div className="h-[400px] w-full rounded-xl overflow-hidden border border-gray-800 shadow-lg mt-8">
            <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
                {/* ... TileLayer ... */}
                {/* ... Polygon ... */}

                {/* Render only valid devices */}
                {validDevices.map((device) => (
                    <Marker
                        key={device.device_id}
                        position={[device.sensorData.lat, device.sensorData.lon]}
                    >
                        {/* ... Popup ... */}
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
};

export default RiskMapView;