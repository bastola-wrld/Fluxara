// client/src/App.jsx
import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import MetricCards from './components/metriccards'
import FacilityTable from './components/facilitytable'
import Map from './components/map'
import EmissionChart from './components/emissionchart'
import InvertPanel from './components/invertpanel'

// Pages
import FacilityDetail from './pages/FacilityDetail'
import FacilitiesPage from './pages/FacilitiesPage'
import ReportsPage from './pages/ReportsPage'
import AlertsPage from './pages/AlertsPage'
import AdminPanel      from './pages/AdminPanel'
import CompanyPanel    from './pages/CompanyPanel'
import GovernmentPanel from './pages/GovernmentPanel'
import LoginPage       from './pages/LoginPage'

import { api } from './api'
import { theme } from './design_system'

function Dashboard() {
    const [facilities, setFacilities] = useState([])
    const [metrics, setMetrics] = useState([
        { label: 'TOTAL FACILITIES', value: '...', sub: 'Permian Basin', gold: false },
        { label: 'HIGH RISK', value: '...', sub: 'Requires attention', gold: true },
        { label: 'AVG EMISSIONS',  value: '...', sub: 'kg/hr across all sites', gold: false },
        { label: 'SYSTEM ACCURACY', value: '96.2%', sub: 'vs ground truth',    gold: false },
    ])
    const [timeseries, setTimeseries] = useState(null)
    const [selected, setSelected] = useState(null)
    const [loading, setLoading] = useState(true)
    const [adminOrgs, setAdminOrgs] = useState([])
    const navigate = useNavigate()
    const role = localStorage.getItem("role")

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await api.getFacilities();
                setFacilities(data);
                
                const highRisk = data.filter(f => f.risk_level === 'high').length;
                const avgEpa = data.reduce((acc, f) => acc + (f.epa_reported || 0), 0) / data.length;
                
                setMetrics([
                    { label: 'TOTAL FACILITIES', value: data.length.toString(), sub: 'Global Registry', gold: false },
                    { label: 'HIGH RISK', value: highRisk.toString(), sub: 'Requires attention', gold: true },
                    { label: 'AVG EMISSIONS',  value: `${(avgEpa/1000).toFixed(1)}k`, sub: 'kg/hr across all sites', gold: false },
                    { label: 'SYSTEM ACCURACY', value: '96.2%', sub: 'vs ground truth',    gold: false },
                ]);

                const tsData = await api.getTimeseries();
                setTimeseries(tsData);

                if (role === 'admin') {
                    const orgs = await api.getAdminOrganisations();
                    setAdminOrgs(orgs);
                }
            } catch (e) {
                console.error("Failed to fetch dashboard data:", e)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const handleSelect = (f) => {
        setSelected(f)
        navigate(`/facility/${f.id}`)
    }

    if (loading) return (
        <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: theme.colors.background, color: theme.colors.primary, fontFamily: 'serif' }}>
            Initializing satellite link...
        </div>
    )

    return (
        <main style={{ padding: '2rem', maxWidth: 1600, margin: '0 auto' }}>
            <MetricCards metrics={metrics} />
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
                <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    <Map facilities={facilities} selected={selected} onSelect={handleSelect} />
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                        <FacilityTable facilities={facilities} selected={selected} onSelect={handleSelect} />
                        {timeseries && <EmissionChart data={timeseries} />}
                    </div>

                    {role === 'admin' && adminOrgs.length > 0 && (
                        <div style={{ background: theme.colors.surface, borderRadius: theme.radius.md, padding: '1.5rem', boxShadow: theme.shadows.md }}>
                            <h2 style={{ margin: '0 0 1rem 0', color: theme.colors.primary, fontFamily: 'serif' }}>Registered Organisations</h2>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                                    <thead>
                                        <tr style={{ borderBottom: `2px solid ${theme.colors.border}` }}>
                                            {['ID', 'NAME', 'TYPE', 'COUNTRY', 'PLAN', 'STATUS'].map(h => (
                                                <th key={h} style={{ padding: '1rem', fontWeight: 'bold', color: theme.colors.textMuted }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {adminOrgs.slice(0, 5).map(o => (
                                            <tr key={o.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                                <td style={{ padding: '1rem' }}>{o.id}</td>
                                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{o.name}</td>
                                                <td style={{ padding: '1rem' }}>{o.org_type.toUpperCase()}</td>
                                                <td style={{ padding: '1rem' }}>{o.country || '-'}</td>
                                                <td style={{ padding: '1rem' }}>{o.plan.toUpperCase()}</td>
                                                <td style={{ padding: '1rem' }}>{o.active ? 'Active' : 'Disabled'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
                <div style={{ gridColumn: 'span 1' }}>
                    <InvertPanel />
                </div>
            </div>
        </main>
    )
}

function Navbar({ alertCount }) {
    const navigate = useNavigate()
    const location = useLocation()
    
    const role = localStorage.getItem("role")
    
    let links = []
    if (role === "admin") {
        links = [
            { name: 'Admin Overview', path: '/admin' },
            { name: 'Dashboard', path: '/' },
            { name: 'Facilities', path: '/facilities' },
            { name: 'Reports', path: '/reports' },
            { name: 'Alerts', path: '/alerts', badge: alertCount },
        ]
    } else if (role === "company") {
        links = [
            { name: 'My Dashboard', path: `/company/1` }, // Mock orgId
            { name: 'Facilities', path: '/facilities' },
            { name: 'Reports', path: '/reports' },
            { name: 'Alerts', path: '/alerts', badge: alertCount },
        ]
    } else if (role === "government") {
        links = [
            { name: 'National Oversight', path: '/government' },
            { name: 'Facilities', path: '/facilities' },
            { name: 'Alerts', path: '/alerts', badge: alertCount },
        ]
    }

    return (
        <nav style={{
            background: theme.colors.primary,
            color: theme.colors.secondary,
            padding: '1rem 2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 50,
            boxShadow: theme.shadows.lg
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3rem' }}>
                <div 
                    style={{ fontSize: '1.5rem', fontWeight: 'bold', letterSpacing: '-1px', cursor: 'pointer' }} 
                    onClick={() => navigate('/')}
                >
                    FLUXARA
                </div>
                <div style={{ display: 'flex', gap: '2rem' }}>
                    {links.map(link => (
                        <button 
                            key={link.path}
                            onClick={() => navigate(link.path)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: theme.colors.secondary,
                                opacity: location.pathname === link.path ? 1 : 0.6,
                                fontSize: '0.8rem',
                                fontWeight: 'bold',
                                textTransform: 'uppercase',
                                letterSpacing: '0.1em',
                                cursor: 'pointer',
                                position: 'relative',
                                padding: '0.5rem 0'
                            }}
                        >
                            {link.name}
                            {link.badge > 0 && (
                                <span style={{ marginLeft: '0.5rem', background: '#ef4444', color: 'white', fontSize: '0.7rem', padding: '2px 6px', borderRadius: '10px' }}>
                                    {link.badge}
                                </span>
                            )}
                            {location.pathname === link.path && (
                                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px', background: theme.colors.secondary, borderRadius: '2px' }} />
                            )}
                        </button>
                    ))}
                </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', fontWeight: 'bold', opacity: 0.8 }}>
                    <div style={{ width: '8px', height: '8px', background: '#4ade80', borderRadius: '50%' }}></div>
                    {role?.toUpperCase()} ACCESS · LIVE
                </div>
                <button 
                    onClick={() => {
                        localStorage.clear()
                        navigate("/login")
                        window.location.reload()
                    }}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        color: 'white',
                        fontSize: '0.7rem',
                        padding: '6px 12px',
                        borderRadius: theme.radius.sm,
                        cursor: 'pointer',
                        fontWeight: 'bold'
                    }}
                >
                    LOGOUT
                </button>
            </div>
        </nav>
    )
}

function Footer() {
    return (
        <footer style={{
            background: theme.colors.primary,
            color: theme.colors.secondary,
            padding: '3rem 2rem',
            marginTop: '4rem',
            borderTop: `1px solid rgba(255,255,255,0.1)`
        }}>
            <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '3rem' }}>
                <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '1rem' }}>FLUXARA</div>
                    <p style={{ fontSize: '0.75rem', opacity: 0.6, lineHeight: 1.6 }}>
                        Converting satellite observation into source-attributed intelligence. 
                        Physics-constrained neural inversion for a transparent methane economy.
                    </p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem', fontWeight: 'bold', opacity: 0.6 }}>
                    <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Privacy Policy</a>
                    <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Terms of Service</a>
                    <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Methodology</a>
                </div>
                <div style={{ textAlign: 'right', fontSize: '0.75rem', opacity: 0.4 }}>
                    © 2026 FLUXARA TECHNOLOGIES INC.<br/>
                    ALL SATELLITE DATA VIA ESA TROPOMI
                </div>
            </div>
        </footer>
    )
}

export default function App() {
    const [alertCount, setAlertCount] = useState(0)
    const navigate = useNavigate()
    const location = useLocation()

    useEffect(() => {
        const role = localStorage.getItem("role")
        if (!role && location.pathname !== "/login") {
            navigate("/login")
        }

        api.getAlertCount()
            .then(data => setAlertCount(data.unresolved))
            .catch(console.error)
            
        const interval = setInterval(() => {
            api.getAlertCount().then(data => setAlertCount(data.unresolved))
        }, 30000)
        return () => clearInterval(interval)
    }, [location.pathname])

    const hideNav = location.pathname === "/login"

    return (
        <div style={{ minHeight: '100vh', background: theme.colors.background, fontFamily: 'serif' }}>
            {!hideNav && <Navbar alertCount={alertCount} />}
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<Dashboard />} />
                <Route path="/facility/:id" element={<FacilityDetail />} />
                <Route path="/facilities" element={<FacilitiesPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                
                <Route path="/admin"          element={<AdminPanel />} />
                <Route path="/company/:orgId" element={<CompanyPanel />} />
                <Route path="/government"     element={<GovernmentPanel />} />
            </Routes>
            {!hideNav && <Footer />}
        </div>
    )
}