import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { theme } from '../design_system'
import MetricCards from '../components/metriccards'
import ReportLibrary from '../components/ReportLibrary'

export default function CompanyPanel() {
    const { orgId } = useParams()
    const [activeTab, setActiveTab] = useState('Overview')
    const [stats, setStats] = useState(null)
    const [facilities, setFacilities] = useState([])
    const [inversions, setInversions] = useState([])
    const [alerts, setAlerts] = useState([])
    const [reports, setReports] = useState([])
    const navigate = useNavigate()

    useEffect(() => {
        const role = localStorage.getItem("role")
        if (role !== "company" && role !== "admin") navigate("/")
        
        fetchData()
    }, [orgId])

    const fetchData = async () => {
        try {
            const [overview, f, i, a, r] = await Promise.all([
                api.getCompanyOverview(orgId),
                api.getCompanyFacilities(orgId),
                api.getCompanyInversions(orgId),
                api.getCompanyAlerts(orgId),
                api.getCompanyReports(orgId)
            ])
            setStats(overview)
            setFacilities(f)
            setInversions(i)
            setAlerts(a)
            setReports(r)
        } catch (err) {
            console.error("Failed to fetch company data", err)
        }
    }

    const tabs = ['Overview', 'Facilities', 'Inversions', 'Alerts', 'Reports']

    const renderOverview = () => {
        if (!stats) return null
        const metrics = [
            { label: 'FACILITIES', value: stats.facilities, sub: 'Total sites' },
            { label: 'HIGH RISK', value: stats.high_risk, sub: 'Requires mitigation', gold: stats.high_risk > 0 },
            { label: 'UNRESOLVED ALERTS', value: stats.unresolved_alerts, sub: 'Needs review' },
            { label: 'TOTAL INVERSIONS', value: stats.inversions, sub: 'Satellite runs' },
        ]
        return (
            <div>
                <MetricCards metrics={metrics} />
                <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div style={{ background: theme.colors.surface, borderRadius: theme.radius.md, padding: '1.5rem', boxShadow: theme.shadows.md }}>
                        <h3 style={{ margin: '0 0 1rem 0' }}>Facility Summary</h3>
                        {facilities.slice(0, 5).map(f => (
                            <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: `1px solid ${theme.colors.border}` }}>
                                <span>{f.name}</span>
                                <span style={{ fontWeight: 'bold', color: f.discrepancy_pct > 20 ? theme.colors.riskHigh : theme.colors.text }}>
                                    {f.discrepancy_pct ? `${f.discrepancy_pct}% diff` : 'N/A'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
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

    const downloadCorpPDF = async () => {
        try {
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${baseUrl}/reports/company/${orgId}/pdf`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Fluxara_Corporate_Audit.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error("Corp PDF download failed:", e);
        }
    }

    return (
        <div style={{ padding: '2rem', maxWidth: 1600, margin: '0 auto' }}>
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <h1 style={{ margin: 0, color: theme.colors.primary, letterSpacing: '-1px' }}>Company Dashboard</h1>
                    <button 
                        onClick={downloadCorpPDF}
                        style={{
                            padding: '0.5rem 1rem',
                            borderRadius: '8px',
                            background: theme.colors.secondary,
                            color: theme.colors.primary,
                            border: `1px solid ${theme.colors.primary}`,
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            fontSize: '0.8rem'
                        }}
                    >
                        Download PDF Audit
                    </button>
                </div>
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
                                cursor: 'pointer'
                            }}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {activeTab === 'Overview' && renderOverview()}

            {activeTab === 'Facilities' && (
                <div>
                    <div style={{ marginBottom: '1rem', textAlign: 'right' }}>
                        <button style={{ background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>+ Add Facility</button>
                    </div>
                    {renderTable(
                        ['NAME', 'SECTOR', 'EPA REPORTED', 'FLUXARA LATEST', 'DISCREPANCY', 'ACTIONS'],
                        facilities,
                        (f) => (
                            <tr key={f.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{f.name}</td>
                                <td style={{ padding: '1rem' }}>{f.sector}</td>
                                <td style={{ padding: '1rem' }}>{f.epa_reported} kg/hr</td>
                                <td style={{ padding: '1rem' }}>{f.fluxara_latest} kg/hr</td>
                                <td style={{ padding: '1rem' }}>
                                    <span style={{ color: f.discrepancy_pct > 20 ? theme.colors.riskHigh : theme.colors.text }}>
                                        {f.discrepancy_pct}%
                                    </span>
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <button onClick={() => api.removeFacility(f.id).then(fetchData)} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>Remove</button>
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Inversions' && renderTable(
                ['DATE', 'EMISSION RATE', 'CONFIDENCE', 'COMPUTE MS'],
                inversions,
                (i) => (
                    <tr key={i.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                        <td style={{ padding: '1rem' }}>{i.date}</td>
                        <td style={{ padding: '1rem', fontWeight: 'bold' }}>{i.emission_rate} kg/hr</td>
                        <td style={{ padding: '1rem' }}>
                            <div style={{ width: '100px', height: '10px', background: '#eee', borderRadius: '5px', overflow: 'hidden' }}>
                                <div style={{ width: `${i.confidence * 100}%`, height: '100%', background: theme.colors.primary }} />
                            </div>
                            <span style={{ fontSize: '0.7rem' }}>{(i.confidence * 100).toFixed(0)}%</span>
                        </td>
                        <td style={{ padding: '1rem' }}>{i.compute_ms}ms</td>
                    </tr>
                )
            )}

            {activeTab === 'Alerts' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {alerts.map(a => (
                        <div key={a.id} style={{ background: theme.colors.surface, borderRadius: theme.radius.md, padding: '1.5rem', boxShadow: theme.shadows.md, borderLeft: `5px solid ${a.severity === 'high' ? theme.colors.riskHigh : '#f59e0b'}` }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                <span style={{ fontWeight: 'bold', color: theme.colors.textMuted }}>ALERT #{a.id}</span>
                                <span style={{ fontSize: '0.8rem', color: theme.colors.textMuted }}>{new Date(a.created_at).toLocaleDateString()}</span>
                            </div>
                            <p style={{ margin: '0 0 1.5rem 0', fontWeight: 'bold' }}>{a.message}</p>
                            <button onClick={() => api.resolveCompanyAlert(a.id).then(fetchData)} style={{ width: '100%', background: theme.colors.primary, color: 'white', border: 'none', padding: '0.75rem', borderRadius: theme.radius.sm, fontWeight: 'bold', cursor: 'pointer' }}>Resolve Alert</button>
                        </div>
                    ))}
                </div>
            )}

            {activeTab === 'Reports' && (
                <div>
                    <div style={{ marginBottom: '2rem' }}>
                        <h2 style={{ margin: '0 0 0.5rem 0' }}>Available Reports</h2>
                        <p style={{ margin: 0, color: theme.colors.textMuted, fontSize: '0.85rem' }}>Reports generated by Fluxara administrators for your organisation.</p>
                    </div>

                    <ReportLibrary />

                    {reports.length > 0 && (
                        <>
                            <h3 style={{ margin: '2rem 0 1rem 0', color: theme.colors.textMuted }}>Legacy Report Records</h3>
                            {renderTable(
                                ['DATE', 'TYPE', 'STATUS', 'EMISSIONS', 'DOWNLOAD'],
                                reports,
                                (r) => (
                                    <tr key={r.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                        <td style={{ padding: '1rem' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                                        <td style={{ padding: '1rem' }}>{r.report_type}</td>
                                        <td style={{ padding: '1rem' }}>{r.status}</td>
                                        <td style={{ padding: '1rem', fontWeight: 'bold' }}>{r.total_emissions ? `${r.total_emissions} kg` : 'Calculating...'}</td>
                                        <td style={{ padding: '1rem' }}>
                                            {r.pdf_path ? <a href={r.pdf_path} style={{ color: theme.colors.primary, fontWeight: 'bold' }}>PDF Download</a> : '-'}
                                        </td>
                                    </tr>
                                )
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    )
}
