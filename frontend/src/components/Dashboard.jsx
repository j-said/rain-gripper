import React from 'react';
import { useDeviceStore } from '../store/deviceStore';
import FieldCard from './FieldCard';

const Dashboard = () => {
  const devices = useDeviceStore((state) => state.devices);
  const isLoading = useDeviceStore((state) => state.isLoading);
  const error = useDeviceStore((state) => state.error);

  // Початкове завантаження
  if (isLoading && devices.length === 0) {
    return <div className="status-message">Завантаження даних з API...</div>;
  }

  // Помилка при першому завантаженні
  if (error && devices.length === 0) {
    return <div className="status-message error">Помилка: {error}</div>;
  }
  
  // Немає пристроїв (API повернуло '[]')
  if (devices.length === 0) {
    return <div className="status-message">Не знайдено пристроїв для цього клієнта.</div>
  }

  return (
    <>
      {/* Помилка під час оновлення (не блокує UI) */}
      {error && <div className="status-message error">Помилка оновлення: {error}</div>}
      
      <div className="dashboard-grid">
        {devices.map(device => (
          <FieldCard key={device.id} device={device} />
        ))}
      </div>
    </>
  );
};

export default Dashboard;