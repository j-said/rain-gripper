import { useEffect } from 'react';
import { useDeviceStore } from '../store/deviceStore';

// Ми більше не будемо використовувати 'shallow' або 'useDeviceActions'

export const useDataSimulation = (intervalMs = 10000) => {
  // --- НОВИЙ ПІДХІД ---
  // Ми витягуємо кожну функцію окремо.
  // Оскільки самі функції ніколи не змінюються,
  // Zustand не буде викликати зайвих ре-рендерів.
  const fetchDevices = useDeviceStore((state) => state.fetchDevices);
  const simulateUpdates = useDeviceStore((state) => state.simulateUpdates);

  useEffect(() => {
    // 1. Завантажуємо початкові дані
    fetchDevices();

    // 2. Встановлюємо інтервал
    const intervalId = setInterval(() => {
      simulateUpdates();
    }, intervalMs);

    // 3. Прибираємо інтервал
    return () => clearInterval(intervalId);
    
    // Ці залежності тепер 100% стабільні, оскільки
    // fetchDevices і simulateUpdates - це стабільні функції.
  }, [fetchDevices, simulateUpdates, intervalMs]);
};