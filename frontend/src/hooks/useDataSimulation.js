import { useEffect } from 'react';
import { useDeviceStore } from '../store/deviceStore';

export const useDataSimulation = (intervalMs = 10000) => {
  // Використовуємо правильні назви функцій
  const fetchSensorData = useDeviceStore((state) => state.fetchSensorData);
  const updateDeviceData = useDeviceStore((state) => state.updateDeviceData);

  useEffect(() => {
    fetchSensorData(); // Початкове завантаження

    const intervalId = setInterval(() => {
      updateDeviceData(); // Оновлення кожні 10 сек
    }, intervalMs);

    return () => clearInterval(intervalId);
    
  }, [fetchSensorData, updateDeviceData, intervalMs]);
};