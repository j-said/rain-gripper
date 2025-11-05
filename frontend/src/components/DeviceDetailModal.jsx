import React from 'react';
import { useDeviceStore } from '../store/deviceStore';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

const DeviceDetailModal = () => {
  const isOpen = useDeviceStore((state) => state.isModalOpen);
  const isLoading = useDeviceStore((state) => state.isModalLoading);
  const history = useDeviceStore((state) => state.deviceHistory);
  const close = useDeviceStore((state) => state.closeDeviceModal);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" onClick={close}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-button" onClick={close}>&times;</button>
        
        <h2>Погодинний Рівень Води (останні 24 год)</h2>

        <div className="chart-container">
          {isLoading ? (
            <div className="status-message">Завантаження даних графіка...</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={history}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#34495e" />
                <XAxis dataKey="time" stroke="#ecf0f1" />
                <YAxis label={{ value: 'Рівень (см)', angle: -90, position: 'insideLeft', fill: '#ecf0f1' }} stroke="#ecf0f1" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#2c3a47', border: 'none' }} 
                  labelStyle={{ color: '#ecf0f1' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="waterLevel" 
                  stroke="#3498db" 
                  strokeWidth={2}
                  activeDot={{ r: 8 }} 
                  name="Рівень Води (см)"
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