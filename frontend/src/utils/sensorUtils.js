// Extract key metrics from the messy JSON payload
export const parseSensorPayload = (payload) => {
  if (!payload) return null;

  const data = {
    airTemp: payload.air_temp ?? payload.temp ?? payload.temperature ?? null,
    soilTemp: payload.soil_temp ?? null,
    airHum: payload.air_humidity ?? payload.humidity ?? null,
    soilHum: payload.soil_humidity ?? null,
    waterLevel: payload.water_level ?? 0,
    lat: payload.latitude || payload.lat,
    lon: payload.longitude || payload.lon,
  };

  // Logic: Calculate Alert Status
  // Example: High water level (>80) OR very dry soil (<10)
  const isDanger = (data.waterLevel > 80) || (data.soilHum !== null && data.soilHum < 10);
  const isWarning = (data.waterLevel > 50);

  let status = 'normal';
  if (isDanger) status = 'danger';
  else if (isWarning) status = 'warning';

  return { ...data, status };
};