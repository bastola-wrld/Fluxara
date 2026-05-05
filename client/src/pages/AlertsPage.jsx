// client/src/pages/AlertsPage.jsx
import { useState, useEffect } from 'react'
import { api } from '../api'
import { theme } from '../design_system'

export default function AlertsPage() {
    const [alerts, setAlerts] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getAlerts()
            .then(setAlerts)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    const resolve = async (id) => {
        try {
            await api.resolveAlert(id)
            setAlerts(alerts.map(a => a.id === id ? { ...a, resolved: true } : a))
        } catch (e) {
            console.error("Failed to resolve alert:", e)
        }
    }

    if (loading) return <div style={{ padding: '4rem', textAlign: 'center', color: theme.colors.primary, fontFamily: 'serif' }}>Loading alert telemetry...</div>

    return (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto', fontFamily: 'serif' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '2rem' }}>Anomaly Alerts</h1>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {alerts.map(alert => (
                    <div key={alert.id} style={{
                        background: 'white',
                        padding: '1.5rem',
                        borderRadius: '12px',
                        border: `1px solid ${alert.resolved ? theme.colors.border : theme.colors.riskHigh}`,
                        borderLeft: `6px solid ${alert.severity === 'Critical' ? '#9b1c1c' : '#d97706'}`,
                        boxShadow: theme.shadows.sm,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        opacity: alert.resolved ? 0.6 : 1,
                        transition: 'opacity 0.3s'
                    }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                <span style={{ fontSize: '0.65rem', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.1em', color: alert.severity === 'Critical' ? '#9b1c1c' : '#d97706' }}>
                                    {alert.severity}
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{new Date(alert.created_at).toLocaleString()}</span>
                            </div>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '0.25rem', margin: 0 }}>{alert.facility_name}</h3>
                            <p style={{ fontSize: '0.9rem', color: theme.colors.textMuted, margin: 0 }}>{alert.message}</p>
                        </div>
                        
                        {!alert.resolved ? (
                            <button 
                                onClick={() => resolve(alert.id)}
                                style={{
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px',
                                    background: theme.colors.primary,
                                    color: 'white',
                                    border: 'none',
                                    fontSize: '0.8rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                Mark Resolved
                            </button>
                        ) : (
                            <span style={{ color: '#059669', fontWeight: 'bold', fontSize: '0.8rem' }}>✓ RESOLVED</span>
                        )}
                    </div>
                ))}
                
                {alerts.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '4rem', color: '#9ca3af', fontStyle: 'italic' }}>
                        No active anomalies detected.
                    </div>
                )}
            </div>
        </div>
    )
}
