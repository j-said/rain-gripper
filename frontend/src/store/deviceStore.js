import { create } from 'zustand';
import { MOCK_DEVICES } from '../data/mockData';

// --- Допоміжні функції ---

// Обчислюємо "Field Risk Score" (0-100)
// Це проста логіка, ви можете її ускладнити
const calculateRiskScore = (moisture, waterLevel) => {
  // Ризик від вологості (60% ваги)
  const moistureRisk = Math.min(moisture, 100); // 0-100
  
  // Ризик від рівня води (40% ваги)
  // Припустимо, 50 см - це 100% ризику
  const waterRisk = Math.min((waterLevel / 50) * 100, 100); 

  const totalRisk = moistureRisk * 0.6 + waterRisk * 0.4;
  return Math.round(totalRisk);
};

// Визначаємо стан поля на основі ризику
const getCondition = (riskScore) => {
  if (riskScore > 75) return 'Небезпечно';
  if (riskScore > 45) return 'Дуже волого';
  if (riskScore > 25) return 'Помірно';
  return 'Сухо';
};

// --- Стор Zustand ---

export const useDeviceStore = create((set) => ({
  devices: [],

  // 1. Дія: Завантажити початкові дані
  fetchDevices: () => {
    const initialData = MOCK_DEVICES.map((dev) => {
      const riskScore = calculateRiskScore(dev.moisture, dev.waterLevel);
      return {
        ...dev,
        riskScore,
        condition: getCondition(riskScore),
        lastUpdated: new Date(),
      };
    });
    set({ devices: initialData });
  },

  // 2. Дія: Симулювати оновлення (для setInterval)
  simulateUpdates: () => {
    set((state) => ({
      devices: state.devices.map((dev) => {
        // Симулюємо зміну даних +/- 5%
        const moistureChange = (Math.random() - 0.5) * 10;
        const waterLevelChange = (Math.random() - 0.5) * 4;

        const newMoisture = Math.max(0, Math.min(100, dev.moisture + moistureChange));
        const newWaterLevel = Math.max(0, dev.waterLevel + waterLevelChange);
        
        const newRiskScore = calculateRiskScore(newMoisture, newWaterLevel);
        const newCondition = getCondition(newRiskScore);

        // 10% шанс, що пристрій "вийде з мережі"
        const newStatus = dev.status === 'Online' && Math.random() < 0.1 ? 'Offline' : 'Online';

        return {
          ...dev,
          moisture: newMoisture,
          waterLevel: newWaterLevel,
          riskScore: newRiskScore,
          condition: newCondition,
          status: newStatus,
          lastUpdated: new Date(),
        };
      }),
    }));
  },
}));