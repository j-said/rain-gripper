import React from 'react';
import RiskGauge from './RiskGauge';
import { useDeviceStore } from '../store/deviceStore';

// Маленький компонент-індикатор статусу
const StatusIndicator = ({ status }) => (
  <span 
    className={`status-dot ${status === 'Online' ? 'online' : 'offline'}`}
    title={status}
  ></span>
);

const FieldCard = ({ device }) => {
  // Отримуємо дію зі стору
  const sendCommand = useDeviceStore((state) => state.sendCommand);

  // Функція для отримання CSS-класу на основі ризику
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

  // Обробник для кнопки команди
  const handleSendCommand = () => {
    // Тіло запиту 'CommandRequest'
    // Використовуємо 'action' як підтверджено з main.py
    const commandBody = {
      action: "REBOOT_DEVICE", // Приклад команди
      parameters: { delay_ms: 500 } // Приклад параметрів
    };
    
    console.log(`Надсилаю команду до ${device.id}...`);
    sendCommand(device.id, commandBody);
  };

  return (
    <div className={`field-card ${cardRiskClass}`}>
      
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
          <div className="metric">
            <span>Координати</span>
            <strong>{device.lat.toFixed(3)}, {device.lon.toFixed(3)}</strong>
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
        
        {/* Нова кнопка команди */}
        <button 
          onClick={handleSendCommand} 
          className="command-button"
          disabled={device.status !== 'Online'} // Блокуємо, якщо офлайн
        >
          Надіслати команду
        </button>
        
        <div className="update-time">
          <StatusIndicator status={device.status} />
          Оновлено: {device.lastUpdated.toLocaleTimeString('uk-UA')}
        </div>
      </div>
    </div>
  );
};

export default FieldCard;