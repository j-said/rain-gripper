import React from 'react';
import { useDeviceStore } from '../store/deviceStore';
import FieldCard from './FieldCard';

const Dashboard = () => {
  // Отримуємо актуальні дані з нашого стору
  const devices = useDeviceStore((state) => state.devices);

  if (devices.length === 0) {
    return <div>Завантаження симуляції...</div>;
  }

  return (
    <div className="dashboard-grid">
      {devices.map(device => (
        <FieldCard key={device.id} device={device} />
      ))}
    </div>
  );
};

export default Dashboard;