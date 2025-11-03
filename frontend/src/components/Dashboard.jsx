import React from 'react';
import { useDeviceStore } from '../store/deviceStore';
import FieldCard from './FieldCard';

const Dashboard = () => {
  // 1. Отримуємо РЕАЛЬНІ дані з API (зараз це '[]')
  const apiDevices = useDeviceStore((state) => state.devices);
  const isLoading = useDeviceStore((state) => state.isLoading);
  const error = useDeviceStore((state) => state.error);

  // --- ↓↓↓ КОД ДЛЯ ТЕСТУВАННЯ КНОПКИ POST ↓↓↓ ---
  // Створюємо фейковий пристрій
  const MOCK_FOR_TESTING = {
    id: 'test-device-001',
    fieldName: 'Тестова Ділянка (Mock)',
    moisture: 50,
    waterLevel: 15,
    lat: 50.4501,
    lon: 30.5234,
    status: 'Online',
    riskScore: 40,
    condition: 'Помірно',
    lastUpdated: new Date(), // Створюємо безпечний об'єкт Дати
  };

  // 2. Об'єднуємо реальні дані з API з нашим тестовим пристроєм
  const devices = [...apiDevices, MOCK_FOR_TESTING];
  // --- ↑↑↑ КІНЕЦЬ ТЕСТОВОГО КОДУ ↑↑↑ ---


  // 3. Логіка відображення
  
  // Показуємо завантаження, лише якщо API ще не відповіло
  if (isLoading && apiDevices.length === 0) {
    return <div className="status-message">Завантаження даних з API...</div>;
  }

  // Показуємо помилку, лише якщо API дало збій
  if (error && apiDevices.length === 0) {
    return <div className="status-message error">Помилка: {error}</div>;
  }
  
  // Оскільки 'devices' тепер завжди містить наш MOCK_FOR_TESTING,
  // ми більше не покажемо "Не знайдено пристроїв",
  // а натомість відрендеримо список.
  return (
    <>
      {/* Показуємо помилку оновлення, якщо вона є */}
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