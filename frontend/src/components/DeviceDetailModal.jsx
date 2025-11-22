import React, { useState } from 'react';
import { X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

const DeviceDetailModal = ({ device, onClose }) => {
    const [metric, setMetric] = useState('waterLevel');

    if (!device) return null;

    // Use the REAL history passed from the Dashboard
    // If no history exists, default to empty array to prevent crashes
    const history = device.history || [];

    // Format data for the chart (ensure timestamp is readable)
    const chartData = history.map(log => ({
        ...log,
        time: log.timestamp ? format(new Date(log.timestamp), 'HH:mm') : '--',
    }));

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
            <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden border border-gray-100">

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">{device.device_name}</h2>
                        <div className="flex items-center space-x-2">
                            <span className="text-gray-500 text-sm">ID: {device.local_id}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${device.isOnline ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                {device.isOnline ? 'Online' : 'Offline'}
                            </span>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Controls */}
                <div className="flex space-x-2 p-6 pb-2">
                    {['waterLevel', 'airTemp', 'soilHum'].map(m => (
                        <button
                            key={m}
                            onClick={() => setMetric(m)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all border ${metric === m
                                    ? 'bg-green-50 border-green-200 text-green-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            {m === 'waterLevel' ? 'Water Level' : m === 'airTemp' ? 'Temperature' : 'Soil Humidity'}
                        </button>
                    ))}
                </div>

                {/* Chart */}
                <div className="h-[400px] p-6 w-full">
                    {chartData.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-100 rounded-xl">
                            <p>No historical data available for the last 24 hours.</p>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} tickLine={false} />
                                <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#fff', borderColor: '#e5e7eb', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    itemStyle={{ color: '#374151', fontWeight: 600 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey={metric}
                                    stroke={metric === 'waterLevel' ? '#3b82f6' : metric === 'airTemp' ? '#ef4444' : '#22c55e'}
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, fill: '#fff', strokeWidth: 2 }}
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