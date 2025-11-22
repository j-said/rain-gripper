import React, { useState } from 'react';
import { X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

// Simple Hook to mock history data (Replace with API call later if endpoint exists)
// Currently your backend only supports getting "latest" data slice easily.
// We will simulate 24h history for now or query the existing slice endpoint.
const useDeviceHistory = (deviceId) => {
    // TODO: Call /api/v1/data/?start_date=...&end_date=...
    // For now, we generate realistic looking data based on the ID
    const data = Array.from({ length: 24 }).map((_, i) => ({
        time: format(new Date().setHours(new Date().getHours() - (23 - i)), 'HH:00'),
        waterLevel: 20 + Math.random() * 10,
        temp: 15 + Math.random() * 5,
        humidity: 60 + Math.random() * 20
    }));
    return { data, isLoading: false };
};

const DeviceDetailModal = ({ deviceId, onClose }) => {
    const { data: history, isLoading } = useDeviceHistory(deviceId);
    const [metric, setMetric] = useState('waterLevel'); // 'waterLevel' | 'temp' | 'humidity'

    if (!deviceId) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-gray-900 w-full max-w-4xl rounded-2xl border border-gray-800 shadow-2xl overflow-hidden">

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-800">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Device Analysis</h2>
                        <p className="text-gray-400 text-sm">ID: {deviceId}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Controls */}
                <div className="flex space-x-4 p-6 pb-0">
                    {['waterLevel', 'temp', 'humidity'].map(m => (
                        <button
                            key={m}
                            onClick={() => setMetric(m)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${metric === m
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                }`}
                        >
                            {m === 'waterLevel' ? 'Water Level' : m === 'temp' ? 'Temperature' : 'Humidity'}
                        </button>
                    ))}
                </div>

                {/* Chart */}
                <div className="h-[400px] p-6 w-full">
                    {isLoading ? (
                        <div className="h-full flex items-center justify-center text-gray-500">Loading history...</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={history}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                                <YAxis stroke="#9ca3af" fontSize={12} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#f3f4f6' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey={metric}
                                    stroke={metric === 'waterLevel' ? '#3b82f6' : metric === 'temp' ? '#ef4444' : '#10b981'}
                                    strokeWidth={3}
                                    dot={{ fill: '#1f2937', strokeWidth: 2 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </div>

            </div>
        </div>
    );
};

export default DeviceDetailModal;