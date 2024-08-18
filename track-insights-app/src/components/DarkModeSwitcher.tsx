import React, { useState, useEffect } from "react";
import { MoonIcon, SunIcon } from "./Icons.tsx";
import { Switch } from "@nextui-org/react";

const DarkModeSwitcher: React.FC = () => {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("dark-mode") === "true";
  });

  useEffect(() => {
    document.body.className = darkMode ? "dark" : "";
    localStorage.setItem("dark-mode", darkMode.toString());
  }, [darkMode]);

  return (
    <Switch
      defaultSelected
      size="sm"
      color="default"
      onChange={() => setDarkMode(!darkMode)}
      thumbIcon={({ isSelected, className }) =>
        isSelected ? (
          <SunIcon className={className} />
        ) : (
          <MoonIcon className={className} />
        )
      }
    />
  );
}

export default DarkModeSwitcher;