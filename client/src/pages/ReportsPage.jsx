// client/src/pages/ReportsPage.jsx
import { useState, useEffect } from 'react'
import { api } from '../api'
import { theme } from '../design_system'

export default function ReportsPage() {
    const [reports, setReports] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getReports()
            .then(setReports)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <div style={{ padding: '4rem', textAlign: 'center', color: theme.colors.primary, fontFamily: 'serif' }}>Loading compliance archive...</div>

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', fontFamily: 'serif' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '2rem' }}>Compliance & MRV Reports</h1>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                {reports.map(report => (
                    <div key={report.id} style={{
                        background: 'white',
                        padding: '2rem',
                        borderRadius: '16px',
                        border: `1px solid ${theme.colors.border}`,
                        boxShadow: theme.shadows.sm,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        transition: 'transform 0.2s',
                        cursor: 'pointer'
                    }}
                    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
                    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                                <div style={{ width: '40px', height: '40px', background: '#F5F0EB', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem' }}>
                                    📄
                                </div>
                                <span style={{ fontSize: '0.65rem', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.1em', color: theme.colors.textMuted }}>
                                    {report.report_type}
                                </span>
                            </div>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '0.5rem', margin: 0 }}>{report.title}</h3>
                            <p style={{ fontSize: '0.85rem', color: theme.colors.textMuted, marginBottom: '1.5rem', margin: 0 }}>{report.summary}</p>
                        </div>
                        
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid #f3f4f6`, paddingTop: '1.5rem' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.colors.primary }}>{report.date_from} to {report.date_to}</span>
                            <button style={{
                                background: 'none',
                                border: 'none',
                                color: theme.colors.primary,
                                fontSize: '0.75rem',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                textDecoration: 'underline'
                            }}>
                                Download PDF
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
