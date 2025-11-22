import { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import DeviceCard from '../components/DeviceCard';
import DeviceDetailModal from '../components/DeviceDetailModal';
import { Loader2, Layers } from 'lucide-react';

const Dashboard = () => {
    const { groupedData, isLoading } = useDashboardData();
    // Change state to hold the OBJECT, not just the ID
    const [selectedDevice, setSelectedDevice] = useState(null);

    if (isLoading) {
        return (
            <div className="flex h-[50vh] items-center justify-center text-green-600">
                <Loader2 className="animate-spin w-10 h-10" />
                <span className="ml-3 text-lg font-medium">Syncing Fields...</span>
            </div>
        );
    }

    return (
        <div className="space-y-10 pb-20">
            {/* ... Header ... */}
            <div className="flex justify-between items-center border-b border-gray-200 pb-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Farm Overview</h1>
                    <p className="text-gray-500">Real-time monitoring & analysis</p>
                </div>
                <div className="bg-green-100 text-green-800 px-4 py-1 rounded-full text-sm font-bold">
                    System Online
                </div>
            </div>

            {groupedData.map((group) => (
                <div key={group.group_id} className="animate-in fade-in duration-500">
                    <div className="flex items-center mb-4 space-x-2">
                        <Layers className="text-green-600" size={20} />
                        <h2 className="text-xl font-bold text-gray-800">{group.display_name}</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {group.devices.map(device => (
                            <DeviceCard
                                key={device.device_id}
                                device={device}
                                // Pass the entire device object on click
                                onClick={() => setSelectedDevice(device)}
                            />
                        ))}
                    </div>
                </div>
            ))}

            {/* Updated Modal Implementation */}
            {selectedDevice && (
                <DeviceDetailModal
                    device={selectedDevice}
                    onClose={() => setSelectedDevice(null)}
                />
            )}
        </div>
    );
};

export default Dashboard;