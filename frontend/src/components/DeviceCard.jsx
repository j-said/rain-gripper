import { Droplets, Thermometer, AlertTriangle, Sprout } from 'lucide-react'; // Added Sprout import
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import clsx from 'clsx';

// --- Mini Sparkline Component ---
const Sparkline = ({ data, dataKey, color }) => {
    if (!data || data.length === 0) return null;

    const hasValidData = data.some(point => {
        const val = point[dataKey];
        return val !== null && val !== undefined && !isNaN(Number(val));
    });

    // If this sensor doesn't produce this metric, REMOVE the chart.
    if (!hasValidData) return null;

    return (
        <div className="h-10 w-24 ml-4">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <YAxis domain={['auto', 'auto']} hide />
                    <Line
                        type="monotone"
                        dataKey={dataKey}
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                        connectNulls={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

// --- Metric Row Component ---
const MetricRow = ({ label, value, unit, icon: Icon, history, dataKey, color }) => (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 h-14">
        <div className="flex items-center space-x-3">
            <div className={`p-1.5 rounded-md bg-${color}-100 text-${color}-600`}>
                <Icon size={16} />
            </div>
            <div>
                <p className="text-xs text-gray-500 font-medium uppercase">{label}</p>
                <p className="font-bold text-gray-800">
                    {value !== null && value !== 'N/A' && value !== undefined
                        ? value
                        : '--'}
                    <span className="text-xs font-normal text-gray-400 ml-0.5">{unit}</span>
                </p>
            </div>
        </div>

        {/* Only renders if data exists */}
        <Sparkline data={history} dataKey={dataKey} color={color === 'blue' ? '#3b82f6' : color === 'red' ? '#ef4444' : '#22c55e'} />
    </div>
);

const DeviceCard = ({ device, onClick }) => {
    const { sensorData, device_name, model, history } = device;
    const status = sensorData.status;

    return (
        <div
            onClick={onClick}
            className={clsx(
                "bg-white rounded-xl shadow-sm border transition-all duration-200 hover:shadow-md cursor-pointer overflow-hidden",
                status === 'danger' ? "border-red-500 border-2" : "border-gray-200"
            )}
        >
            {/* Card Header */}
            <div className={clsx(
                "px-4 py-3 flex justify-between items-center",
                status === 'danger' ? "bg-red-50" : "bg-gray-50"
            )}>
                <div className="overflow-hidden">
                    <h3 className="font-bold text-gray-800 truncate">{device_name}</h3>
                    <p className="text-xs text-gray-500 truncate">{model || 'Unknown Model'}</p>
                </div>
                {status === 'danger' ? (
                    <AlertTriangle className="text-red-500 shrink-0" size={20} />
                ) : (
                    <div className={clsx("w-2.5 h-2.5 rounded-full shrink-0", device.isOnline ? "bg-green-500" : "bg-gray-400")} />
                )}
            </div>

            {/* Card Body: Metrics & Charts */}
            <div className="p-4 pt-2">
                {/* Water Level */}
                <MetricRow
                    label="Water Lvl"
                    value={sensorData.waterLevel}
                    unit="cm"
                    icon={Droplets}
                    history={history}
                    dataKey="waterLevel"
                    color="blue"
                />

                {/* Air Temp */}
                <MetricRow
                    label="Air Temp"
                    value={sensorData.airTemp}
                    unit="°C"
                    icon={Thermometer}
                    history={history}
                    dataKey="airTemp"
                    color="red"
                />

                {/* Soil Humidity */}
                <MetricRow
                    label="Soil Hum"
                    value={sensorData.soilHum}
                    unit="%"
                    icon={Sprout}
                    history={history}
                    dataKey="soilHum"
                    color="green"
                />
            </div>

            {/* Footer: Timestamp */}
            <div className="bg-gray-50 px-4 py-2 text-[10px] text-gray-400 flex justify-between items-center">
                <span>ID: {device.local_id}</span>
                <span>
                    {device.lastSeen
                        ? new Date(device.lastSeen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : 'Never seen'}
                </span>
            </div>
        </div>
    );
};

export default DeviceCard;