import { useEffect } from 'react';
import { useDeviceStore } from '../store/deviceStore';

// Цей хук запускає початкове завантаження
// і встановлює інтервал для оновлення даних
export const useDataSimulation = (intervalMs = 10000) => {
  // Витягуємо дії зі стору (стабільний метод)
  const fetchDevices = useDeviceStore((state) => state.fetchDevices);
  const updateDeviceData = useDeviceStore((state) => state.updateDeviceData);

  useEffect(() => {
    // 1. Завантажуємо дані 1 раз при старті
    fetchDevices();

    // 2. Встановлюємо інтервал для оновлення
    const intervalId = setInterval(() => {
      updateDeviceData();
    }, intervalMs);

    // 3. Прибираємо інтервал при демонтажі
    return () => clearInterval(intervalId);
    
  }, [fetchDevices, updateDeviceData, intervalMs]);
};