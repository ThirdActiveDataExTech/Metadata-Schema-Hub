import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="header">
      <Link to="/" className="header-logo">
        <h1>Active Metadata Management</h1>
      </Link>
    </header>
  )
}
