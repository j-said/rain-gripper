import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { parseSensorPayload } from '../utils/sensorUtils';
import { subDays } from 'date-fns';

// Fetch Groups
const fetchGroups = async () => {
  const { data } = await api.get('/api/v1/groups/');
  return data;
};

// Fetch Devices for a Group
const fetchDevicesForGroup = async (groupId) => {
  const { data } = await api.get(`/api/v1/groups/${groupId}/devices/`);
  return data;
};

// Fetch FULL Sensor History for the last 24h
const fetchSensorHistory = async () => {
  const endDate = new Date();
  const startDate = subDays(endDate, 1); // Last 24 hours
  
  // Use ISO strings for API parameters
  const params = new URLSearchParams({
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString()
  });

  const { data } = await api.get(`/api/v1/data/?${params.toString()}`);
  return data; // Returns flat array of all logs for all user's devices
};

export const useDashboardData = () => {
  const { data: groups, isLoading: loadingGroups } = useQuery({
    queryKey: ['groups'],
    queryFn: fetchGroups,
  });

  const { data: allDevices, isLoading: loadingDevices } = useQuery({
    queryKey: ['allDevices', groups],
    queryFn: async () => {
      if (!groups) return [];
      const promises = groups.map(g => fetchDevicesForGroup(g.group_id));
      const results = await Promise.all(promises);
      return results.flat();
    },
    enabled: !!groups?.length,
  });

  // 3. Poll Sensor History (Last 24h) every 5 mins
  const { data: historyLogs } = useQuery({
    queryKey: ['sensorHistory'],
    queryFn: fetchSensorHistory,
    refetchInterval: 1000 * 60 * 5, 
  });

  //  groups -> devices -> data history
  const groupsWithDevices = groups?.map(group => {
    
    // Filter devices belonging to this group
    const groupDevices = allDevices?.filter(d => d.group_id === group.group_id) || [];

    // Enrich devices with their specific history
    const enrichedDevices = groupDevices.map(device => {
      // Filter logs for this specific device
      const deviceLogs = historyLogs?.filter(log => log.device_id === device.device_id) || [];
      
      // Sort: Newest last (for charts)
      deviceLogs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      const latestLog = deviceLogs[deviceLogs.length - 1];
      const parsedLatest = parseSensorPayload(latestLog?.payload);

      // Map logs to clean history objects for charts
      const cleanHistory = deviceLogs.map(log => ({
        timestamp: log.timestamp,
        ...parseSensorPayload(log.payload)
      }));

      return {
        ...device,
        isOnline: !!latestLog,
        lastSeen: latestLog?.timestamp,
        // Latest snapshot
        sensorData: parsedLatest || { 
          airTemp: null, soilTemp: null, airHum: null, soilHum: null, waterLevel: 0, status: 'offline' 
        },
        // Full history for sparklines
        history: cleanHistory
      };
    });

    return {
      ...group,
      devices: enrichedDevices
    };
  }) || [];

  return {
    groupedData: groupsWithDevices,
    isLoading: loadingGroups || loadingDevices,
  };
};