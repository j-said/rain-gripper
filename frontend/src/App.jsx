import { useDataSimulation } from './hooks/useDataSimulation';
import Dashboard from './components/Dashboard';
import RiskMapView from './components/RiskMapView';

function App() {
  // Запускаємо хук симуляції
  // Він сам завантажить дані та запустить оновлення
  // 10000 мс = 10 секунд, як у завданні
  useDataSimulation(10000); 

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🚜 Моніторинг Стану Полів</h1>
        <p>Панель для операторів транспорту</p>
      </header>
      <main>
        <Dashboard />
        <RiskMapView />
      </main>
    </div>
  );
}

export default App;