import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import Dashboard from './pages/Dashboard.tsx'
import SpeciesBrowser from './pages/SpeciesBrowser.tsx'
import SpeciesDetail from './pages/SpeciesDetail.tsx'
import MapView from './pages/MapView.tsx'

const router = createHashRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'species', element: <SpeciesBrowser /> },
      { path: 'species/:id', element: <SpeciesDetail /> },
      { path: 'map', element: <MapView /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
