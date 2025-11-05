import React from 'react';
import RiskGauge from './RiskGauge';
import { useDeviceStore } from '../store/deviceStore';

const StatusIndicator = ({ status }) => (
  <span 
    className={`status-dot ${status === 'Online' ? 'online' : 'offline'}`}
    title={status}
  ></span>
);

const FieldCard = ({ device }) => {
  const sendCommand = useDeviceStore((state) => state.sendCommand);
  const openDeviceModal = useDeviceStore((state) => state.openDeviceModal); 

  const getConditionClass = (condition) => {
    switch (condition) {
      case 'Небезпечно': return 'condition-danger';
      case 'Дуже волого': return 'condition-high';
      case 'Помірно': return 'condition-moderate';
      case 'Сухо': return 'condition-safe';
      default: return '';
    }
  };
  
  const cardRiskClass = getConditionClass(device.condition);

  const handleSendCommand = (e) => {
    // Зупиняємо "спливання" кліку
    e.stopPropagation(); 
    
    const commandBody = {
      action: "REBOOT_DEVICE", 
      parameters: { delay_ms: 500 }
    };
    sendCommand(device.deviceGroup, commandBody); 
  };
  
  const handleCardClick = () => {
    openDeviceModal(device.id); // Викликаємо дію з ID пристрою
  };

  return (
    <div 
      className={`field-card ${cardRiskClass} clickable`}
      onClick={handleCardClick}
    >
      
      <div className="card-header">
        <h3>{device.fieldName}</h3> 
        <span className="device-id">{device.id}</span>
      </div>

      <div className="card-body">
        <div className="data-metrics">
          <div className="metric">
            <span>Вологість ґрунту</span>
            <strong>{device.moisture.toFixed(1)}%</strong>
          </div>
          <div className="metric">
            <span>Рівень води</span>
            <strong>{device.waterLevel.toFixed(1)} см</strong> 
          </div>
        </div>
        
        <div className="risk-display">
          <RiskGauge score={device.riskScore} />
        </div>
      </div>

      <div className="card-footer">
        <div className={`condition-badge ${cardRiskClass}`}>
          {device.condition}
        </div>
        
        <button 
          onClick={handleSendCommand} 
          className="command-button"
          disabled={device.status !== 'Online' || device.deviceGroup === 'unknown_group'}
        >
          Надіслати команду
        </button>
        
        <div className="update-time">
          <StatusIndicator status={device.status} />
          Оновлено: {new Date(device.lastUpdated).toLocaleTimeString('uk-UA')}
        </div>
      </div>
    </div>
  );
};

export default FieldCard;