import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { useDeviceStore } from '../store/deviceStore';

const RiskMapView = () => {
  const devices = useDeviceStore((state) => state.devices);

  if (devices.length === 0) {
    return null; // Не рендерити карту, якщо немає даних
  }

  // Використаємо координати першого пристрою для центрування карти
  const mapCenter = [devices[0].lat, devices[0].lon];

  return (
    <MapContainer center={mapCenter} zoom={12} className="map-container">
      {/* Це "плитка" карти, основа, яку ми бачимо */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {/* Проходимо по кожному пристрою і ставимо маркер */}
      {devices.map(device => (
        <Marker 
          key={device.id} 
          position={[device.lat, device.lon]}
        >
          {/* Popup - це те, що з'являється при кліку на маркер */}
          <Popup>
            <b>{device.fieldName}</b> ({device.status})
            <br />
            Вологість: {device.moisture.toFixed(1)}%
            <br />
            Рівень води: {device.waterLevel.toFixed(1)} см
            <br />
            <b>Ризик: {device.riskScore} ({device.condition})</b>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default RiskMapView;