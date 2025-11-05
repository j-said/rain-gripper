import { create } from 'zustand';

// --- АДАПТЕР ДАНИХ (ЗГІДНО З seed-db.py) ---
const adaptApiData = (apiDevice) => {
  const payload = apiDevice.payload || {};
  
  // --- Хелпери ---
  const calculateRiskScore = (moisture, waterLevel) => {
    const moistureRisk = Math.min(moisture || 0, 100);
    const waterRisk = Math.min(((waterLevel || 0) / 50) * 100, 100); // 50 см = 100% ризику
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

  const moisture = payload.humidity || 0;
  const waterLevel = payload.water_level || 0;
  const riskScore = calculateRiskScore(moisture, waterLevel);

  return {
    id: apiDevice.device_id, 
    fieldName: apiDevice.device_id,
    deviceGroup: payload.device_group || 'unknown_group', 
    status: payload.is_online ? 'Online' : 'Offline', 
    lat: payload.latitude || 50.4501,  // (Координати за замовчуванням: Київ)
    lon: payload.longitude || 30.5234, 
    moisture: moisture,
    waterLevel: waterLevel,
    lastUpdated: new Date(apiDevice.timestamp),
    riskScore: riskScore,
    condition: getCondition(riskScore),
  };
};

// --- Функція симуляції (для графіка) ---
const generateMockHourlyData = () => {
  const data = [];
  const now = new Date();
  for (let i = 24; i >= 0; i--) {
    data.push({
      time: `${(now.getHours() - i + 24) % 24}:00`,
      waterLevel: Math.random() * 40 + 10,
    });
  }
  return data;
};

// --- Стор Zustand ---
export const useDeviceStore = create((set, get) => ({
  devices: [],
  isLoading: false,
  error: null,
  userId: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', // ID з seed-db

  // --- Стан для модального вікна ---
  isModalOpen: false,
  isModalLoading: false,
  deviceHistory: [], 

  // --- Отримуємо дані про сенсори (З ВИПРАВЛЕННЯМ ДУБЛІКАТІВ) ---
  fetchSensorData: async (startDate = null, endDate = null) => {
    set({ isLoading: true, error: null });
    const userId = get().userId; 
    let url = `/api/v1/data/${userId}`;
    
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
      const sensorData = await response.json(); 

      // --- ↓↓↓ ВИПРАВЛЕННЯ ДУБЛІКАТІВ ↓↓↓ ---
      const uniqueDeviceLogs = new Map();
      for (const log of sensorData) {
        if (!uniqueDeviceLogs.has(log.device_id)) {
          uniqueDeviceLogs.set(log.device_id, log);
        }
      }
      const latestLogs = Array.from(uniqueDeviceLogs.values());
      const adaptedDevices = latestLogs.map(adaptApiData);
      
      set({ devices: adaptedDevices, isLoading: false });
      // --- ↑↑↑ КІНЕЦЬ ВИПРАВЛЕННЯ ---

    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // --- Оновлення для polling ---
  updateDeviceData: () => {
    get().fetchSensorData();
  },

  // --- Дія: Надіслати команду ---
  sendCommand: async (device_group, commandBody) => {
    set({ isLoading: true, error: null });
    const userId = get().userId;
    try {
      const response = await fetch(`/api/v1/command/${userId}/${device_group}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(commandBody),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Помилка команди: ${errorData.detail || response.statusText}`);
      }
      const result = await response.json();
      console.log('Команду надіслано:', result);
      set({ isLoading: false });
      get().fetchSensorData();
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  // --- Дії для модального вікна (СИНХРОННА СИМУЛЯЦІЯ) ---
  fetchDeviceHistory: (deviceId) => {
    set({ isModalLoading: true });
    
    console.warn("API для /api/v1/data/device/ не знайдено. Вмикаю СИНХРОННУ симуляцію графіка.");
    const mockData = generateMockHourlyData();
    
    // Миттєво вимикаємо завантаження і передаємо дані
    set({ deviceHistory: mockData, isModalLoading: false });
  },

  openDeviceModal: (deviceId) => {
    set({ isModalOpen: true });
    get().fetchDeviceHistory(deviceId); 
  },

  closeDeviceModal: () => {
    set({ isModalOpen: false, deviceHistory: [] }); 
  },
}));