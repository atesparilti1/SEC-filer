import { Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { ComparePage } from "./pages/ComparePage";
import { Dashboard } from "./pages/Dashboard";

export default function App() {
  return (
    <div className="min-h-screen bg-canvas">
      <Header />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/compare" element={<ComparePage />} />
      </Routes>
    </div>
  );
}
