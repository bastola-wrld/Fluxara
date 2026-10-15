import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { theme } from '../design_system'
import MetricCards from '../components/metriccards'
import ReportLibrary from '../components/ReportLibrary'

export default function GovernmentPanel() {
    const [activeTab, setActiveTab] = useState('Overview')
    const [country, setCountry] = useState('USA')
    const [sector, setSector] = useState('')
    const [threshold, setThreshold] = useState(20)
    
    const [stats, setStats] = useState(null)
    const [facilities, setFacilities] = useState([])
    const [sectors, setSectors] = useState([])
    const [underreporting, setUnderreporting] = useState(null)
    const [ndc, setNdc] = useState(null)
    const navigate = useNavigate()

    useEffect(() => {
        const role = localStorage.getItem("role")
        if (role !== "government" && role !== "admin") navigate("/")
        
        fetchData()
    }, [country, sector])

    const fetchData = async () => {
        try {
            const [overview, f, s, u, n] = await Promise.all([
                api.getGovOverview(country, sector),
                api.getGovFacilities(country, sector),
                api.getGovSectors(country),
                api.getUnderreporting(threshold, country, sector),
                api.getNDCVerification(country)
            ])
            setStats(overview)
            setFacilities(f)
            setSectors(s)
            setUnderreporting(u)
            setNdc(n)
        } catch (err) {
            console.error("Failed to fetch government data", err)
        }
    }

    const tabs = ['Overview', 'Facilities', 'By Sector', 'Underreporting', 'NDC', 'Reports']

    const renderOverview = () => {
        if (!stats) return null
        const metrics = [
            { label: 'TOTAL SITES', value: stats.total_facilities, sub: country || 'Global' },
            { label: 'HIGH RISK', value: stats.high_risk, sub: 'Targeted for inspection' },
            { label: 'UNDERREPORTING', value: `${stats.underreporting_pct}%`, sub: 'Above 20% threshold', gold: stats.underreporting_pct > 15 },
            { label: 'EPA REPORTED', value: `${(stats.total_epa_reported_kg_hr / 1000).toFixed(1)}k`, sub: 'kg/hr' },
            { label: 'FLUXARA SATELLITE', value: `${(stats.total_fluxara_kg_hr / 1000).toFixed(1)}k`, sub: 'kg/hr' },
            { label: 'DISCREPANCY', value: `${(stats.discrepancy_kg_hr / 1000).toFixed(1)}k`, sub: 'kg/hr variance' },
        ]
        return (
            <div>
                {stats.underreporting_pct > 20 && (
                    <div style={{ background: '#fee2e2', border: '1px solid #ef4444', color: '#b91c1c', padding: '1rem', borderRadius: theme.radius.sm, marginBottom: '2rem', fontWeight: 'bold' }}>
                        CRITICAL WARNING: Aggregate underreporting in {country} {sector} sector exceeds 20%. Systematic audit recommended.
                    </div>
                )}
                <MetricCards metrics={metrics} />
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

    return (
        <div style={{ padding: '2rem', maxWidth: 1600, margin: '0 auto' }}>
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ margin: 0, color: theme.colors.primary, letterSpacing: '-1px' }}>National Oversight</h1>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <select value={country} onChange={(e) => setCountry(e.target.value)} style={{ padding: '0.5rem', borderRadius: theme.radius.sm, border: `1px solid ${theme.colors.border}` }}>
                        <option value="USA">United States</option>
                        <option value="CAN">Canada</option>
                        <option value="MEX">Mexico</option>
                    </select>
                    <select value={sector} onChange={(e) => setSector(e.target.value)} style={{ padding: '0.5rem', borderRadius: theme.radius.sm, border: `1px solid ${theme.colors.border}` }}>
                        <option value="">All Sectors</option>
                        <option value="O&G">Oil & Gas</option>
                        <option value="Waste">Waste</option>
                        <option value="Agriculture">Agriculture</option>
                    </select>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
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

            {activeTab === 'Overview' && renderOverview()}

            {activeTab === 'Facilities' && renderTable(
                ['NAME', 'COUNTRY', 'SECTOR', 'EPA', 'FLUXARA', 'DISCREPANCY'],
                facilities,
                (f) => (
                    <tr key={f.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                        <td style={{ padding: '1rem', fontWeight: 'bold' }}>{f.name}</td>
                        <td style={{ padding: '1rem' }}>{f.country}</td>
                        <td style={{ padding: '1rem' }}>{f.sector}</td>
                        <td style={{ padding: '1rem' }}>{f.epa_reported}</td>
                        <td style={{ padding: '1rem' }}>{f.fluxara_latest ?? 'No data'}</td>
                        <td style={{ padding: '1rem' }}>
                            <span style={{ 
                                padding: '4px 8px', 
                                borderRadius: '4px', 
                                background: f.underreporting ? '#fee2e2' : 'transparent',
                                color: f.underreporting ? '#ef4444' : theme.colors.text,
                                fontWeight: 'bold'
                            }}>
                                {f.discrepancy_pct}%
                            </span>
                        </td>
                    </tr>
                )
            )}

            {activeTab === 'By Sector' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
                    {sectors.map(s => (
                        <div key={s.sector} style={{ background: theme.colors.surface, borderRadius: theme.radius.md, padding: '1.5rem', boxShadow: theme.shadows.md }}>
                            <h3 style={{ margin: '0 0 1rem 0', color: theme.colors.primary }}>{s.sector}</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Sites:</span>
                                    <span style={{ fontWeight: 'bold' }}>{s.facility_count}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Fluxara:</span>
                                    <span style={{ fontWeight: 'bold' }}>{s.total_fluxara_kg_hr} kg/hr</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>High Risk:</span>
                                    <span style={{ fontWeight: 'bold', color: theme.colors.riskHigh }}>{s.high_risk}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {activeTab === 'Underreporting' && (
                <div>
                    <div style={{ marginBottom: '2rem', background: theme.colors.surface, padding: '1.5rem', borderRadius: theme.radius.md, boxShadow: theme.shadows.md }}>
                        <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Threshold Slider: {threshold}%</label>
                        <input 
                            type="range" min="0" max="100" value={threshold} 
                            onChange={(e) => setThreshold(e.target.value)} 
                            style={{ width: '100%', accentColor: theme.colors.primary }}
                        />
                        <button onClick={fetchData} style={{ marginTop: '1rem', background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: theme.radius.sm, cursor: 'pointer' }}>Update Rank</button>
                    </div>
                    {underreporting && renderTable(
                        ['RANK', 'FACILITY', 'SECTOR', 'DISCREPANCY %', 'RISK LEVEL'],
                        underreporting.facilities,
                        (f, idx) => (
                            <tr key={f.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem' }}>{idx + 1}</td>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{f.name}</td>
                                <td style={{ padding: '1rem' }}>{f.sector}</td>
                                <td style={{ padding: '1rem', color: '#ef4444', fontWeight: 'bold' }}>{f.discrepancy_pct}%</td>
                                <td style={{ padding: '1rem' }}>{f.risk_level.toUpperCase()}</td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'NDC' && ndc && (
                <div style={{ background: theme.colors.surface, padding: '2rem', borderRadius: theme.radius.md, boxShadow: theme.shadows.md }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: `2px solid ${theme.colors.border}`, paddingBottom: '1rem' }}>
                        <h2 style={{ margin: 0 }}>Paris Agreement NDC Verification: {ndc.country}</h2>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: theme.colors.primary }}>{ndc.total_fluxara_kg_hr} kg/hr</div>
                            <div style={{ fontSize: '0.8rem', color: theme.colors.textMuted }}>SATELLITE DERIVED NATIONAL TOTAL</div>
                        </div>
                    </div>
                    {renderTable(
                        ['SECTOR', 'COUNT', 'EPA REPORTED', 'FLUXARA SATELLITE', 'VARIANCE'],
                        ndc.sector_breakdown,
                        (s) => (
                            <tr key={s.sector} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{s.sector}</td>
                                <td style={{ padding: '1rem' }}>{s.facility_count}</td>
                                <td style={{ padding: '1rem' }}>{s.epa_kg_hr}</td>
                                <td style={{ padding: '1rem' }}>{s.fluxara_kg_hr}</td>
                                <td style={{ padding: '1rem', color: s.fluxara_kg_hr > s.epa_kg_hr ? '#ef4444' : '#10b981' }}>
                                    {(s.fluxara_kg_hr - s.epa_kg_hr).toFixed(1)} kg/hr
                                </td>
                            </tr>
                        )
                    )}
                </div>
            )}

            {activeTab === 'Reports' && (
                <div>
                    <div style={{ marginBottom: '2rem' }}>
                        <h2 style={{ margin: '0 0 0.5rem 0' }}>Intelligence Reports</h2>
                        <p style={{ margin: 0, color: theme.colors.textMuted, fontSize: '0.85rem' }}>Satellite monitoring reports generated for your jurisdiction.</p>
                    </div>
                    <ReportLibrary />
                </div>
            )}
        </div>
    )
}
