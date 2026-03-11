import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="app">
      <Header />
      <div className="main-content">
        <Sidebar />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
