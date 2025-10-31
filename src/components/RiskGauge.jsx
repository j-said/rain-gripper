import React from 'react';

const RiskGauge = ({ score }) => {
  const getScoreColor = (score) => {
    if (score > 75) return '#e74c3c'; // Червоний
    if (score > 45) return '#f39c12'; // Помаранчевий
    if (score > 25) return '#f1c40f'; // Жовтий
    return '#2ecc71'; // Зелений
  };

  const color = getScoreColor(score);
  // Магія CSS: 3.6 - це 360 градусів / 100 очок
  const gradient = `conic-gradient(${color} ${score * 3.6}deg, #34495e 0deg)`;

  return (
    <div className="gauge-container">
      <div className="gauge-dial" style={{ background: gradient }}>
        <div className="gauge-value">{Math.round(score)}</div>
      </div>
      <div className="gauge-label">Рівень Ризику</div>
    </div>
  );
};

export default RiskGauge;