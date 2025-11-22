import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { parseSensorPayload } from '../utils/sensorUtils';

// 1. Fetch all groups for the user
const fetchGroups = async () => {
  const { data } = await api.get('/api/v1/groups/');
  return data;
};

// 2. Fetch devices for a specific group
const fetchDevicesForGroup = async (groupId) => {
  const { data } = await api.get(`/api/v1/groups/${groupId}/devices/`);
  return data;
};

// 3. Fetch latest sensor readings (Polled)
const fetchSensorData = async () => {
  // We ask for data from 24 hours ago to now to ensure we get the LATEST reading
  const { data } = await api.get('/api/v1/data/');
  return data;
};

export const useDashboardData = () => {
  // A. Get Groups
  const { data: groups, isLoading: loadingGroups } = useQuery({
    queryKey: ['groups'],
    queryFn: fetchGroups,
  });

  // B. Get Devices (Run only when groups are loaded)
  // We define a query for EACH group to get its devices
  const { data: allDevices, isLoading: loadingDevices } = useQuery({
    queryKey: ['allDevices', groups],
    queryFn: async () => {
      if (!groups) return [];
      const promises = groups.map(g => fetchDevicesForGroup(g.group_id));
      const results = await Promise.all(promises);
      // Flatten [[dev1], [dev2, dev3]] -> [dev1, dev2, dev3]
      return results.flat();
    },
    enabled: !!groups?.length,
  });

  // C. Poll Sensor Data (Every 10 seconds)
  const { data: sensorLogs } = useQuery({
    queryKey: ['sensorData'],
    queryFn: fetchSensorData,
    refetchInterval: 10000, // 10 seconds
  });

  // D. MERGE LOGIC
  const mergedDevices = allDevices?.map(device => {
    // Find the latest log
    const deviceLogs = sensorLogs?.filter(log => log.device_id === device.device_id) || [];
    const latestLog = deviceLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];

    const parsedData = parseSensorPayload(latestLog?.payload);

    return {
      ...device,
      isOnline: !!latestLog,
      lastSeen: latestLog?.timestamp,
      sensorData: parsedData || {
        // FALLBACK VALUES FOR OFFLINE DEVICES
        airTemp: 'N/A',
        soilTemp: 'N/A',
        airHum: 'N/A',
        soilHum: 'N/A',
        waterLevel: 0,
        status: 'offline',
        // FIX: Add default coordinates (e.g., Kyiv) if no data exists
        lat: 50.4501,
        lon: 30.5234
      }
    };
  }) || [];

  return {
    devices: mergedDevices,
    isLoading: loadingGroups || loadingDevices,
  };
};