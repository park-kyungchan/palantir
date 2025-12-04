import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/home/HomePage";
import { AnalysisPage } from "./pages/analysis/AnalysisPage";
import { reportWebVitals } from "./lib/observability";

// Initialize Observability
reportWebVitals();

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analyze" element={<AnalysisPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;