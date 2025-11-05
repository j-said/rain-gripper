import { useDataSimulation } from './hooks/useDataSimulation';
import Dashboard from './components/Dashboard';
import RiskMapView from './components/RiskMapView';
import DeviceDetailModal from './components/DeviceDetailModal'; 

function App() {
  useDataSimulation(10000); // 10 секунд

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🚜 Моніторинг Стану Полів (MVP)</h1>
        <p>Панель для операторів транспорту</p>
      </header>
      <main>
        <Dashboard /> 
        <RiskMapView />
        
        {/* Компонент модального вікна (сам вирішує, коли бути видимим) */}
        <DeviceDetailModal /> 
      </main>
    </div>
  );
}

export default App;