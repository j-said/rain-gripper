import { create } from 'zustand';

// Ця функція перетворює дані з вашої схеми `SensorDataResponse`
// у формат, який очікує наш фронтенд (UI).
const adaptApiData = (apiDevice) => {
  // apiDevice - це об'єкт SensorDataResponse
  // { id: 1, created_at: "...", customer_id: "...", sub_device_id: "...", payload: {...} }

  // --- Хелпери ---
  const calculateRiskScore = (moisture, waterLevel) => {
    const moistureRisk = Math.min(moisture || 0, 100);
    const waterRisk = Math.min(((waterLevel || 0) / 50) * 100, 100);
    const totalRisk = moistureRisk * 0.6 + waterRisk * 0.4;
    return Math.round(totalRisk);
  };
  const getCondition = (riskScore) => {
    if (riskScore > 75) return 'Небезпечно';
    if (riskScore > 45) return 'Дуже волого';
    if (riskScore > 25) return 'Помірно';
    return 'Сухо';
  };
  // --- Кінець хелперів ---

  // 1. Безпечно отримуємо 'payload', навіть якщо він null
  const payload = apiDevice.payload || {};

  // 2. !!! ОСТАННЄ ПРИПУЩЕННЯ !!!
  // Нам потрібно знати, як називаються ключі *всередині* 'payload'.
  // Я припускаю, що вони називаються 'moisture', 'water_level_cm' тощо.
  // **Якщо дані не з'являться, вам потрібно перевірити ці назви ключів.**
  const moisture = payload.moisture || 0;
  const waterLevel = payload.water_level_cm || 0;
  const lat = payload.latitude || 50.45;
  const lon = payload.longitude || 30.52;
  const status = payload.is_online ? 'Online' : 'Offline';

  // 3. Обчислюємо ризик на основі даних з payload
  const riskScore = calculateRiskScore(moisture, waterLevel);

  // 4. Повертаємо об'єкт, який очікує наш UI
  return {
    // Ми використовуємо 'sub_device_id' як ID для UI
    id: apiDevice.sub_device_id,
    fieldName: apiDevice.sub_device_id,
    moisture: moisture,
    waterLevel: waterLevel,
    lat: lat,
    lon: lon,
    status: status,
    riskScore: riskScore,
    condition: getCondition(riskScore),
    // Використовуємо 'created_at' з основного об'єкта
    lastUpdated: new Date(apiDevice.created_at),
  };
};

// --- Стор Zustand ---
export const useDeviceStore = create((set, get) => ({
  devices: [],
  isLoading: false,
  error: null,
  customerId: 'customer_demo_id_123', // ID клієнта для MVP

  // --- Дія: Отримати дані з GET /api/v1/data/{customer_id} ---
  fetchDevices: async (startDate = null, endDate = null) => {
    set({ isLoading: true, error: null });
    const customerId = get().customerId;

    let url = `/api/v1/data/${customerId}`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate.toISOString());
    if (endDate) params.append('end_date', endDate.toISOString());

    const queryString = params.toString();
    if (queryString) url += `?${queryString}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Не вдалося завантажити дані');
      }

      const sensorData = await response.json(); // Отримуємо List[SensorDataResponse]
      
      // Використовуємо наш новий адаптер
      const adaptedDevices = sensorData.map(adaptApiData);
      
      set({ devices: adaptedDevices, isLoading: false });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // --- Дія: Оновлення даних (для polling) ---
  updateDeviceData: () => {
    get().fetchDevices();
  },

  // --- Дія: Надіслати команду POST /api/v1/command/{...} ---
  sendCommand: async (sub_device_id, commandBody) => {
    set({ isLoading: true, error: null });
    const customerId = get().customerId;

    try {
      const response = await fetch(`/api/v1/command/${customerId}/${sub_device_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(commandBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Помилка команди: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('Команду надіслано, відповідь:', result);
      set({ isLoading: false });
      
      get().fetchDevices();
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },
}));