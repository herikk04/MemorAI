import { ThemeProvider } from "@/components/theme/theme-provider";
import DashboardPage from "@/pages/DashboardPage";

function App() {
  return (
    <ThemeProvider defaultTheme="system">
      <DashboardPage />
    </ThemeProvider>
  );
}

export default App;
