import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { BrowserRouter as Router } from 'react-router-dom'
import { NextUIProvider } from "@nextui-org/react";

import "./i18n";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <NextUIProvider>
      <Router>
        <App/>
      </Router>
    </NextUIProvider>
  </StrictMode>,
)
