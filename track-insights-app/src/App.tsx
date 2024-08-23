import Navbar from "./components/Navbar.tsx";
import React from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { NextUIProvider } from "@nextui-org/react";
import Overview from "./pages/Overview.tsx";
import Bestlist from "./components/Bestlist/Bestlist.tsx";
import Records from "./pages/Records.tsx";
import Calculator from "./pages/Calculator.tsx";
import Profile from "./pages/Profile.tsx";
import { Toaster } from "sonner";

const App: React.FC = () => {
  const navigate = useNavigate();

  return (
    <NextUIProvider navigate={navigate}>
      <main className="min-h-screen text-foreground bg-background">
        <Navbar/>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/bestlist" element={<Bestlist />} />
          <Route path="/records" element={<Records />} />
          <Route path="/calculator" element={<Calculator />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        <Toaster />
      </main>
    </NextUIProvider>
);
}

export default App
