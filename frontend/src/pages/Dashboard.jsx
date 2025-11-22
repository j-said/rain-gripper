import { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import DeviceCard from '../components/DeviceCard';
import RiskMapView from '../components/RiskMapView'; // Import Map
import DeviceDetailModal from '../components/DeviceDetailModal'; // Import Modal
import { Loader2 } from 'lucide-react';

const Dashboard = () => {
    const { devices, isLoading } = useDashboardData();
    const [selectedDeviceId, setSelectedDeviceId] = useState(null);

    if (isLoading) {
        return (
            <div className="flex h-[50vh] items-center justify-center text-blue-500">
                <Loader2 className="animate-spin w-8 h-8" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* 1. Stats Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
            </div>

            {/* 2. Device Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {devices.map(device => (
                    <DeviceCard
                        key={device.device_id}
                        device={device}
                        onClick={() => setSelectedDeviceId(device.device_id)}
                    />
                ))}
            </div>

            {/* 3. The Map */}
            <RiskMapView />

            {/* 4. The Modal (Conditionall Rendered) */}
            {selectedDeviceId && (
                <DeviceDetailModal
                    deviceId={selectedDeviceId}
                    onClose={() => setSelectedDeviceId(null)}
                />
            )}
        </div>
    );
};

export default Dashboard;