import { Droplets, Thermometer, Wind, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

const Metric = ({ icon: Icon, label, value, unit }) => (
    <div className="flex flex-col items-center bg-gray-800/50 rounded p-2">
        <div className="flex items-center space-x-1 text-gray-400 text-xs uppercase mb-1">
            <Icon size={12} />
            <span>{label}</span>
        </div>
        <div className="font-mono font-bold text-white">
            {value !== 'N/A' && value !== null ? value : '--'}<span className="text-xs text-gray-500 ml-0.5">{unit}</span>
        </div>
    </div>
);

const DeviceCard = ({ device, onClick }) => {
    const { sensorData, device_name, model } = device;
    const status = sensorData.status;

    return (
        <div
            onClick={onClick}
            className={clsx(
                "relative rounded-xl p-5 cursor-pointer transition-all duration-200 border",
                // Dynamic Styles based on Status
                status === 'danger' && "bg-red-900/20 border-red-500/50 hover:bg-red-900/30",
                status === 'warning' && "bg-yellow-900/20 border-yellow-500/50 hover:bg-yellow-900/30",
                status === 'normal' && "bg-gray-800 border-gray-700 hover:border-blue-500",
                status === 'offline' && "bg-gray-900 border-gray-800 opacity-75 grayscale"
            )}
        >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="font-bold text-lg text-white">{device_name}</h3>
                    <p className="text-xs text-gray-400">{model || 'Unknown Model'}</p>
                </div>
                {status === 'danger' && <AlertTriangle className="text-red-500 animate-pulse" />}
            </div>

            {/* 5 Props Grid */}
            <div className="grid grid-cols-2 gap-2 mb-2">
                <Metric icon={Thermometer} label="Air Temp" value={sensorData.airTemp} unit="°C" />
                <Metric icon={Droplets} label="Air Hum" value={sensorData.airHum} unit="%" />
                <Metric icon={Thermometer} label="Soil Temp" value={sensorData.soilTemp} unit="°C" />
                <Metric icon={Droplets} label="Soil Hum" value={sensorData.soilHum} unit="%" />
            </div>

            {/* Water Level (Full Width) */}
            <div className="bg-blue-900/20 rounded p-2 mt-2 border border-blue-500/20">
                <div className="flex justify-between items-center text-sm mb-1">
                    <span className="text-blue-300">Water Level</span>
                    <span className="font-bold text-blue-100">{sensorData.waterLevel} cm</span>
                </div>
                {/* Progress Bar */}
                <div className="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden">
                    <div
                        className="bg-blue-500 h-full transition-all duration-500"
                        style={{ width: `${Math.min(sensorData.waterLevel, 100)}%` }}
                    />
                </div>
            </div>
        </div>
    );
};

export default DeviceCard;