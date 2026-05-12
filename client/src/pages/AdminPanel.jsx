import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { theme } from '../design_system'
import MetricCards from '../components/metriccards'

const TOP_COUNTRIES = [
    "USA", "China", "India", "Japan", "Germany", "UK", "France", "Brazil", "Italy", "Canada",
    "Russia", "South Korea", "Australia", "Spain", "Mexico", "Indonesia", "Netherlands",
    "Saudi Arabia", "Turkey", "Switzerland", "Taiwan", "Poland", "Sweden", "Belgium",
    "Argentina", "Thailand", "Austria", "Norway", "UAE", "Iran", "Nigeria", "South Africa",
    "Egypt", "Pakistan", "Bangladesh", "Vietnam", "Philippines", "Malaysia", "Colombia",
    "Chile", "Singapore", "Denmark", "Finland", "Ireland", "New Zealand", "Portugal", "Peru",
    "Greece", "Czechia", "Romania"
];

export default function AdminPanel() {
    const [activeTab, setActiveTab] = useState('Overview')
    const [stats, setStats] = useState(null)
    const [orgs, setOrgs] = useState([])
    const [users, setUsers] = useState([])
    const [inversions, setInversions] = useState([])
    const [alerts, setAlerts] = useState([])
    
    // Form States
    const [showOrgForm, setShowOrgForm] = useState(false)
    const [newOrg, setNewOrg] = useState({ name: '', org_type: 'company', plan: 'pro', country: 'USA' })
    
    const [showUserForm, setShowUserForm] = useState(false)
    const [newUser, setNewUser] = useState({ email: '', role: 'company', org_id: '' })

    const [showInvForm, setShowInvForm] = useState(false)
    const [newInv, setNewInv] = useState({ facility_id: '', emission_rate: '', confidence: 0.9, date: new Date().toISOString().split('T')[0] })

    const [showAlertForm, setShowAlertForm] = useState(false)
    const [newAlert, setNewAlert] = useState({ facility_id: '', severity: 'high', message: '' })

    // Report Generation State
    const [generatedReports, setGeneratedReports] = useState([])
    const [showReportForm, setShowReportForm] = useState(false)
    const [reportForm, setReportForm] = useState({ report_type: 'summary', region: '', org_id: '', facility_id: '', date_from: '', date_to: '' })
    const [generating, setGenerating] = useState(false)
    const [reportSuccess, setReportSuccess] = useState(null)

    const navigate = useNavigate()

    useEffect(() => {
        const role = localStorage.getItem("role")
        if (role !== "admin") navigate("/")
        
        fetchData()
    }, [])

    const handleRegenerateAll = async () => {
        if (!window.confirm("Trigger regeneration of ALL pre-generated PDFs? This runs in the background and will refresh the manifest for all clients.")) return;
        try {
            setGenerating(true);
            await api.triggerRegeneration();
            setReportSuccess({ title: "Background Regeneration Started", type: "Pre-generated Archive" });
        } catch (e) {
            console.error("Regeneration failed:", e);
            alert("Failed to start regeneration.");
        } finally {
            setGenerating(false);
        }
    }

    const fetchData = async () => {
        try {
            const fetchOrgs = async () => { try { return await api.getAdminOrganisations() } catch (e) { return [] } }
            const fetchUsers = async () => { try { return await api.getAdminUsers() } catch (e) { return [] } }
            const fetchInvs = async () => { try { return await api.getAdminInversions() } catch (e) { return [] } }
            const fetchAlerts = async () => { try { return await api.getAdminAlerts() } catch (e) { return [] } }
            const fetchStats = async () => { try { return await api.getAdminOverview() } catch (e) { return null } }

            const fetchReports = async () => { try { return await api.getReportLibrary() } catch (e) { return [] } }

            const [overview, o, u, i, a, r] = await Promise.all([
                fetchStats(),
                fetchOrgs(),
                fetchUsers(),
                fetchInvs(),
                fetchAlerts(),
                fetchReports()
            ])
            setStats(overview)
            setOrgs(o)
            setUsers(u)
            setInversions(i)
            setAlerts(a)
            setGeneratedReports(r)
        } catch (err) {
            console.error("Failed to fetch admin data", err)
        }
    }

    const handleCreateOrg = async (e) => {
        e.preventDefault()
        try {
            await api.createOrganisation(newOrg)
            setShowOrgForm(false)
            setNewOrg({ name: '', org_type: 'company', plan: 'pro', country: 'USA' })
            fetchData()
        } catch (err) { alert("Failed to create organisation") }
    }

    const handleCreateUser = async (e) => {
        e.preventDefault()
        try {
            await api.createUser(newUser)
            setShowUserForm(false)
            setNewUser({ email: '', role: 'company', org_id: '' })
            fetchData()
        } catch (err) { alert("Failed to create user") }
    }

    const handleCreateInversion = async (e) => {
        e.preventDefault()
        try {
            await api.createAdminInversion({
                ...newInv,
                facility_id: parseInt(newInv.facility_id),
                emission_rate: parseFloat(newInv.emission_rate),
                confidence: parseFloat(newInv.confidence)
            })
            setShowInvForm(false)
            setNewInv({ facility_id: '', emission_rate: '', confidence: 0.9, date: new Date().toISOString().split('T')[0] })
            fetchData()
        } catch (err) { alert("Failed to create inversion") }
    }

    const handleCreateAlert = async (e) => {
        e.preventDefault()
        try {
            await api.createAdminAlert({
                ...newAlert,
                facility_id: parseInt(newAlert.facility_id)
            })
            setShowAlertForm(false)
            setNewAlert({ facility_id: '', severity: 'high', message: '' })
            fetchData()
        } catch (err) { alert("Failed to create alert") }
    }

    const handleGenerateReport = async (e) => {
        e.preventDefault()
        setGenerating(true)
        setReportSuccess(null)
        try {
            const body = {
                report_type: reportForm.report_type,
                region: reportForm.region || null,
                org_id: reportForm.org_id ? parseInt(reportForm.org_id) : null,
                facility_id: reportForm.facility_id ? parseInt(reportForm.facility_id) : null,
                date_from: reportForm.date_from || null,
                date_to: reportForm.date_to || null,
            }
            const result = await api.generateAdminReport(body)
            setReportSuccess(result)
            setShowReportForm(false)
            setReportForm({ report_type: 'summary', region: '', org_id: '', facility_id: '', date_from: '', date_to: '' })
            fetchData()
        } catch (err) {
            console.error('Report generation failed:', err)
            alert('Failed to generate report. Check filters and try again.')
        } finally {
            setGenerating(false)
        }
    }

    const handleDownloadReport = async (report) => {
        try {
            const blob = await api.downloadReport(report.id)
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `Fluxara_${report.report_type}_${report.id}.pdf`
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(url)
        } catch (e) {
            console.error('Download failed:', e)
            alert('Failed to download report.')
        }
    }

    const handleDeleteReport = async (id) => {
        if (!window.confirm('Delete this generated report permanently?')) return
        try {
            await api.deleteGeneratedReport(id)
            fetchData()
        } catch (e) {
            alert('Failed to delete report.')
        }
    }

    const formatFileSize = (bytes) => {
        if (!bytes) return '—'
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    }

    const tabs = ['Overview', 'Organisations', 'Users', 'Inversions', 'Alerts', 'Reports']

    const renderOverview = () => {
        if (!stats) return null
        const metrics = [
            { label: 'ORGANISATIONS', value: stats.organisations, sub: 'Active partners' },
            { label: 'TOTAL USERS', value: stats.users, sub: 'Platform-wide' },
            { label: 'FACILITIES', value: stats.facilities, sub: 'Managed sites' },
            { label: 'INVERSIONS', value: stats.inversions, sub: 'Total compute' },
            { label: 'ALERTS', value: stats.unresolved_alerts, sub: 'Action required', gold: true },
            { label: 'CALLS TODAY', value: stats.api_calls_today, sub: 'Traffic' },
        ]
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <MetricCards metrics={metrics} />
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div>
                        <h2 style={{ margin: '0 0 1rem 0' }}>Recent Organisations</h2>
                        {renderTable(
                            ['ID', 'NAME', 'TYPE', 'COUNTRY', 'PLAN', 'STATUS'],
                            orgs.slice(0, 5),
                            (o) => (
                                <tr key={o.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                    <td style={{ padding: '1rem' }}>{o.id}</td>
                                    <td style={{ padding: '1rem', fontWeight: 'bold' }}>{o.name}</td>
                                    <td style={{ padding: '1rem' }}>{o.org_type.toUpperCase()}</td>
                                    <td style={{ padding: '1rem' }}>{o.country || '-'}</td>
                                    <td style={{ padding: '1rem' }}>{o.plan.toUpperCase()}</td>
                                    <td style={{ padding: '1rem' }}>{o.active ? 'Active' : 'Disabled'}</td>
                                </tr>
                            )
                        )}
                    </div>

                    <div>
                        <h2 style={{ margin: '0 0 1rem 0' }}>Recent Users</h2>
                        {renderTable(
                            ['ID', 'EMAIL', 'ROLE', 'ORG ID'],
                            users.slice(0, 5),
                            (u) => (
                                <tr key={u.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                    <td style={{ padding: '1rem' }}>{u.id}</td>
                                    <td style={{ padding: '1rem', fontWeight: 'bold' }}>{u.email}</td>
                                    <td style={{ padding: '1rem' }}>{u.role}</td>
                                    <td style={{ padding: '1rem' }}>{u.org_id || '-'}</td>
                                </tr>
                            )
                        )}
                    </div>

                    <div>
                        <h2 style={{ margin: '0 0 1rem 0' }}>Recent Inversions</h2>
                        {renderTable(
                            ['ID', 'FACILITY', 'DATE', 'RATE', 'CONF'],
                            inversions.slice(0, 5),
                            (i) => (
                                <tr key={i.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                    <td style={{ padding: '1rem' }}>{i.id}</td>
                                    <td style={{ padding: '1rem' }}>{i.facility_id}</td>
                                    <td style={{ padding: '1rem' }}>{i.date}</td>
                                    <td style={{ padding: '1rem', fontWeight: 'bold' }}>{i.emission_rate} kg/hr</td>
                                    <td style={{ padding: '1rem' }}>{(i.confidence * 100).toFixed(1)}%</td>
                                </tr>
                            )
                        )}
                    </div>

                    <div>
                        <h2 style={{ margin: '0 0 1rem 0' }}>Recent Alerts</h2>
                        {renderTable(
                            ['ID', 'FACILITY', 'SEVERITY', 'MESSAGE'],
                            alerts.slice(0, 5),
                            (a) => (
                                <tr key={a.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                    <td style={{ padding: '1rem' }}>{a.id}</td>
                                    <td style={{ padding: '1rem' }}>{a.facility_id}</td>
                                    <td style={{ padding: '1rem' }}><span style={{ color: a.severity === 'high' ? '#ef4444' : '#f59e0b' }}>{a.severity.toUpperCase()}</span></td>
                                    <td style={{ padding: '1rem' }}>{a.message}</td>
                                </tr>
                            )
                        )}
                    </div>
                </div>
            </div>
        )
    }

    const downloadOrgPDF = async (orgId, orgName) => {
        try {
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${baseUrl}/reports/company/${orgId}/pdf`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            if (!response.ok) throw new Error("Failed to generate PDF");
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Fluxara_Corp_${orgName}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error("Org PDF download failed:", e);
            alert("Could not generate corporate report.");
        }
    }

    const renderTable = (headers, data, renderRow) => (
        <div style={{ background: theme.colors.surface, borderRadius: theme.radius.md, padding: '1rem', overflowX: 'auto', boxShadow: theme.shadows.md }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                    <tr style={{ borderBottom: `2px solid ${theme.colors.border}` }}>
                        {headers.map(h => <th key={h} style={{ padding: '1rem', fontWeight: 'bold', color: theme.colors.textMuted }}>{h}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {data.map(renderRow)}
                </tbody>
            </table>
        </div>
    )

    return (
        <div style={{ padding: '2rem', maxWidth: 1600, margin: '0 auto' }}>
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ margin: 0, color: theme.colors.primary, letterSpacing: '-1px' }}>Admin Control</h1>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    {tabs.map(t => (
                        <button 
                            key={t}
                            onClick={() => setActiveTab(t)}
                            style={{
                                padding: '0.5rem 1.5rem',
                                borderRadius: theme.radius.sm,
                                border: 'none',
                                background: activeTab === t ? theme.colors.primary : 'transparent',
                                color: activeTab === t ? theme.colors.secondary : theme.colors.text,
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {activeTab === 'Organisations' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Registered Customers</h2>
                        <button 
                            onClick={() => setShowOrgForm(!showOrgForm)}
                            style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}
                        >
                            {showOrgForm ? 'Cancel' : '+ New Organisation'}
                        </button>
                    </div>

                    {showOrgForm && (
                        <form onSubmit={handleCreateOrg} style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, marginBottom: '2rem', boxShadow: theme.shadows.md, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>NAME</label>
                                <input required value={newOrg.name} onChange={e => setNewOrg({...newOrg, name: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>TYPE</label>
                                <select value={newOrg.org_type} onChange={e => setNewOrg({...newOrg, org_type: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                    <option value="company">Company</option>
                                    <option value="government">Government</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>COUNTRY</label>
                                <select value={newOrg.country} onChange={e => setNewOrg({...newOrg, country: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                    {TOP_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>PLAN</label>
                                <select value={newOrg.plan} onChange={e => setNewOrg({...newOrg, plan: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                    <option value="pro">Pro</option>
                                    <option value="enterprise">Enterprise</option>
                                    <option value="free">Free</option>
                                </select>
                            </div>
                            <button type="submit" style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 2rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>Create</button>
                        </form>
                    )}

                    {renderTable(
                        ['ID', 'NAME', 'TYPE', 'COUNTRY', 'PLAN', 'STATUS', 'ACTIONS'],
                        orgs,
                        (o) => (
                            <tr key={o.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem' }}>{o.id}</td>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{o.name}</td>
                                <td style={{ padding: '1rem' }}>{o.org_type.toUpperCase()}</td>
                                <td style={{ padding: '1rem' }}>{o.country || '-'}</td>
                                <td style={{ padding: '1rem' }}>{o.plan.toUpperCase()}</td>
                                <td style={{ padding: '1rem' }}>{o.active ? 'Active' : 'Disabled'}</td>
                                <td style={{ padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                    <button onClick={() => downloadOrgPDF(o.id, o.name)} style={{ background: theme.colors.secondary, color: theme.colors.primary, border: `1px solid ${theme.colors.primary}`, padding: '4px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}>PDF</button>
                                    {o.active ? (
                                        <button onClick={() => api.disableOrganisation(o.id).then(fetchData)} style={{ color: '#f59e0b', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>Block</button>
                                    ) : (
                                        <span style={{ color: theme.colors.textMuted, fontSize: '0.8rem' }}>Blocked</span>
                                    )}
                                    <button onClick={() => {
                                        if (window.confirm('Permanently delete organisation?')) {
                                            api.hardDeleteOrganisation(o.id).then(fetchData)
                                        }
                                    }} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>Delete</button>
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Users' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>User Management</h2>
                        <button 
                            onClick={() => setShowUserForm(!showUserForm)}
                            style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}
                        >
                            {showUserForm ? 'Cancel' : '+ Create User'}
                        </button>
                    </div>

                    {showUserForm && (
                        <form onSubmit={handleCreateUser} style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, marginBottom: '2rem', boxShadow: theme.shadows.md, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>EMAIL</label>
                                <input type="email" required value={newUser.email} onChange={e => setNewUser({...newUser, email: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>ROLE</label>
                                <select value={newUser.role} onChange={e => setNewUser({...newUser, role: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                    <option value="admin">Admin</option>
                                    <option value="company">Company User</option>
                                    <option value="government">Government Official</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>ORGANISATION ID</label>
                                <input type="number" required value={newUser.org_id} onChange={e => setNewUser({...newUser, org_id: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <button type="submit" style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 2rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>Create</button>
                        </form>
                    )}

                    {renderTable(
                        ['ID', 'EMAIL', 'ROLE', 'ORG ID', 'STATUS', 'ACTIONS'],
                        users,
                        (u) => (
                            <tr key={u.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem' }}>{u.id}</td>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{u.email}</td>
                                <td style={{ padding: '1rem' }}>{u.role}</td>
                                <td style={{ padding: '1rem' }}>{u.org_id || '-'}</td>
                                <td style={{ padding: '1rem' }}>{u.active ? 'Active' : 'Blocked'}</td>
                                <td style={{ padding: '1rem' }}>
                                    <button onClick={() => api.changeUserRole(u.id, 'admin').then(fetchData)} style={{ color: theme.colors.primary, background: 'none', border: 'none', cursor: 'pointer', marginRight: '1rem' }}>Make Admin</button>
                                    {u.active ? (
                                        <button onClick={() => api.disableUser(u.id).then(fetchData)} style={{ color: '#f59e0b', background: 'none', border: 'none', cursor: 'pointer', marginRight: '1rem' }}>Block</button>
                                    ) : (
                                        <span style={{ color: theme.colors.textMuted, marginRight: '1rem' }}>Blocked</span>
                                    )}
                                    <button onClick={() => {
                                        if (window.confirm('Permanently delete user?')) {
                                            api.hardDeleteUser(u.id).then(fetchData)
                                        }
                                    }} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>Delete</button>
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Overview' && renderOverview()}
            
            {activeTab === 'Inversions' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Inversion Results</h2>
                        <button 
                            onClick={() => setShowInvForm(!showInvForm)}
                            style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}
                        >
                            {showInvForm ? 'Cancel' : '+ New Inversion'}
                        </button>
                    </div>

                    {showInvForm && (
                        <form onSubmit={handleCreateInversion} style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, marginBottom: '2rem', boxShadow: theme.shadows.md, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>FACILITY ID</label>
                                <input type="number" required value={newInv.facility_id} onChange={e => setNewInv({...newInv, facility_id: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>EMISSION RATE (kg/hr)</label>
                                <input type="number" step="0.01" required value={newInv.emission_rate} onChange={e => setNewInv({...newInv, emission_rate: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>CONFIDENCE (0-1)</label>
                                <input type="number" step="0.01" min="0" max="1" required value={newInv.confidence} onChange={e => setNewInv({...newInv, confidence: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>DATE</label>
                                <input type="date" required value={newInv.date} onChange={e => setNewInv({...newInv, date: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <button type="submit" style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 2rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>Create</button>
                        </form>
                    )}

                    {renderTable(
                        ['ID', 'FACILITY', 'DATE', 'EMISSION RATE', 'CONFIDENCE', 'ACTIONS'],
                        inversions,
                        (i) => (
                            <tr key={i.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem' }}>{i.id}</td>
                                <td style={{ padding: '1rem' }}>{i.facility_id}</td>
                                <td style={{ padding: '1rem' }}>{i.date}</td>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{i.emission_rate} kg/hr</td>
                                <td style={{ padding: '1rem' }}>{(i.confidence * 100).toFixed(1)}%</td>
                                <td style={{ padding: '1rem' }}>
                                    <button onClick={() => {
                                        if (window.confirm('Delete inversion result?')) {
                                            api.deleteAdminInversion(i.id).then(fetchData)
                                        }
                                    }} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>Delete</button>
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Alerts' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Active Alerts</h2>
                        <button 
                            onClick={() => setShowAlertForm(!showAlertForm)}
                            style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}
                        >
                            {showAlertForm ? 'Cancel' : '+ New Alert'}
                        </button>
                    </div>

                    {showAlertForm && (
                        <form onSubmit={handleCreateAlert} style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, marginBottom: '2rem', boxShadow: theme.shadows.md, display: 'grid', gridTemplateColumns: '1fr 1fr 2fr auto', gap: '1rem', alignItems: 'end' }}>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>FACILITY ID</label>
                                <input type="number" required value={newAlert.facility_id} onChange={e => setNewAlert({...newAlert, facility_id: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>SEVERITY</label>
                                <select value={newAlert.severity} onChange={e => setNewAlert({...newAlert, severity: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                    <option value="high">High</option>
                                    <option value="medium">Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>MESSAGE</label>
                                <input required value={newAlert.message} onChange={e => setNewAlert({...newAlert, message: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                            </div>
                            <button type="submit" style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 2rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>Create</button>
                        </form>
                    )}

                    {renderTable(
                        ['ID', 'FACILITY', 'SEVERITY', 'MESSAGE', 'DATE', 'ACTIONS'],
                        alerts,
                        (a) => (
                            <tr key={a.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem' }}>{a.id}</td>
                                <td style={{ padding: '1rem' }}>{a.facility_id}</td>
                                <td style={{ padding: '1rem' }}><span style={{ color: a.severity === 'high' ? '#ef4444' : '#f59e0b' }}>{a.severity.toUpperCase()}</span></td>
                                <td style={{ padding: '1rem' }}>{a.message}</td>
                                <td style={{ padding: '1rem' }}>{new Date(a.created_at).toLocaleDateString()}</td>
                                <td style={{ padding: '1rem' }}>
                                    <button onClick={() => {
                                        if (window.confirm('Delete alert?')) {
                                            api.deleteAdminAlert(a.id).then(fetchData)
                                        }
                                    }} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>Delete</button>
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Reports' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>PDF Report Generator</h2>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button 
                                onClick={handleRegenerateAll}
                                disabled={generating}
                                style={{ background: theme.colors.secondary, color: theme.colors.primary, border: `1px solid ${theme.colors.primary}`, padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer', opacity: generating ? 0.5 : 1 }}
                            >
                                {generating ? 'Processing...' : 'Regenerate All Archive'}
                            </button>
                            <button 
                                onClick={() => { setShowReportForm(!showReportForm); setReportSuccess(null); }}
                                style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}
                            >
                                {showReportForm ? 'Cancel' : '+ Generate Custom Report'}
                            </button>
                        </div>
                    </div>

                    {reportSuccess && (
                        <div style={{ background: '#dcfce7', border: '1px solid #22c55e', padding: '1rem', borderRadius: theme.radius.sm, marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong style={{ color: '#166534' }}>Report Generated Successfully</strong>
                                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#166534' }}>
                                    {reportSuccess.title} — {formatFileSize(reportSuccess.file_size)}
                                </p>
                            </div>
                            <button onClick={() => handleDownloadReport(reportSuccess)} style={{ background: '#166534', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Download Now</button>
                        </div>
                    )}

                    {showReportForm && (
                        <form onSubmit={handleGenerateReport} style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, marginBottom: '2rem', boxShadow: theme.shadows.md }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                                <div>
                                    <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>REPORT TYPE</label>
                                    <select value={reportForm.report_type} onChange={e => setReportForm({...reportForm, report_type: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                        <option value="summary">Executive Summary</option>
                                        <option value="full">Full Comprehensive</option>
                                        <option value="compliance">Compliance Audit</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>REGION</label>
                                    <select value={reportForm.region} onChange={e => setReportForm({...reportForm, region: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                        <option value="">Global (All Regions)</option>
                                        {TOP_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>ORGANISATION (Optional)</label>
                                    <select value={reportForm.org_id} onChange={e => setReportForm({...reportForm, org_id: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }}>
                                        <option value="">All Organisations</option>
                                        {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', alignItems: 'end' }}>
                                <div>
                                    <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>DATE FROM (Optional)</label>
                                    <input type="date" value={reportForm.date_from} onChange={e => setReportForm({...reportForm, date_from: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                                </div>
                                <div>
                                    <label style={{ fontSize: '0.7rem', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>DATE TO (Optional)</label>
                                    <input type="date" value={reportForm.date_to} onChange={e => setReportForm({...reportForm, date_to: e.target.value})} style={{ padding: '0.5rem', borderRadius: '4px', border: `1px solid ${theme.colors.border}`, width: '100%' }} />
                                </div>
                                <button 
                                    type="submit" 
                                    disabled={generating}
                                    style={{ 
                                        background: generating ? '#9ca3af' : theme.colors.primary, 
                                        color: 'white', border: 'none', padding: '0.75rem 2rem', 
                                        borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: generating ? 'wait' : 'pointer',
                                        fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
                                    }}
                                >
                                    {generating ? 'Generating...' : 'Generate PDF'}
                                </button>
                            </div>
                        </form>
                    )}

                    <h3 style={{ margin: '2rem 0 1rem 0', color: theme.colors.textMuted }}>Generated Reports Archive</h3>
                    {generatedReports.length === 0 ? (
                        <div style={{ background: theme.colors.surface, padding: '3rem', borderRadius: theme.radius.md, textAlign: 'center', color: theme.colors.textMuted, boxShadow: theme.shadows.md }}>
                            No reports generated yet. Click "+ Generate New Report" to create your first PDF.
                        </div>
                    ) : (
                        renderTable(
                            ['ID', 'TITLE', 'TYPE', 'REGION', 'FACILITIES', 'SIZE', 'CREATED', 'ACTIONS'],
                            generatedReports,
                            (r) => (
                                <tr key={r.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                    <td style={{ padding: '1rem' }}>{r.id}</td>
                                    <td style={{ padding: '1rem', fontWeight: 'bold', maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.title}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold', textTransform: 'uppercase',
                                            background: r.report_type === 'compliance' ? '#fef3c7' : r.report_type === 'full' ? '#dbeafe' : '#dcfce7',
                                            color: r.report_type === 'compliance' ? '#92400e' : r.report_type === 'full' ? '#1e40af' : '#166534'
                                        }}>{r.report_type}</span>
                                    </td>
                                    <td style={{ padding: '1rem' }}>{r.region || 'Global'}</td>
                                    <td style={{ padding: '1rem' }}>{r.total_facilities || '—'}</td>
                                    <td style={{ padding: '1rem' }}>{formatFileSize(r.file_size)}</td>
                                    <td style={{ padding: '1rem' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                                    <td style={{ padding: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                        <button onClick={() => handleDownloadReport(r)} style={{ background: theme.colors.secondary, color: theme.colors.primary, border: `1px solid ${theme.colors.primary}`, padding: '4px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 'bold' }}>Download</button>
                                        <button onClick={() => handleDeleteReport(r.id)} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>Delete</button>
                                    </td>
                                </tr>
                            )
                        )
                    )}
                </div>
            )}
        </div>
    )
}
