// client/src/components/invertpanel.jsx
import { useState } from 'react'
import { api } from '../api'
import { theme } from '../design_system'

export default function InvertPanel() {
    const [form, setForm] = useState({ latitude: '31.85', longitude: '-102.10', date: '2024-06-15' })
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    const run = async () => {
        setLoading(true)
        setResult(null)
        setProcessStep('AQUIRING_SATELLITE_DATA')
        try {
            const data = await api.runInversion({
                latitude: parseFloat(form.latitude),
                longitude: parseFloat(form.longitude),
                date: form.date,
                bbox_deg: 2.0
            })
            setResult(data)
        } catch (e) {
            setResult({ error: e.message || 'Inversion engine failed' })
        }
        setLoading(false)
        setProcessStep(null)
    }

    const [processStep, setProcessStep] = useState(null)

    const inputStyle = {
        width: '100%',
        background: '#FDF8F3',
        border: `1px solid ${theme.colors.border}`,
        borderRadius: '8px',
        padding: '0.5rem 0.75rem',
        fontSize: '0.85rem',
        color: theme.colors.primary,
        fontFamily: 'serif',
        marginTop: '0.5rem',
        outline: 'none'
    }

    const labelStyle = {
        fontSize: '0.55rem',
        fontWeight: 'bold',
        color: '#9ca3af',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
        display: 'block'
    }

    return (
        <div style={{
            background: theme.colors.surface,
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.colors.border}`,
            overflow: 'hidden',
            boxShadow: theme.shadows.sm,
            fontFamily: 'serif',
            height: '100%'
        }}>
            <div style={{
                padding: '1rem 1.25rem',
                borderBottom: `1px solid ${theme.colors.border}`,
                background: theme.colors.primary,
                color: theme.colors.secondary,
                fontSize: '0.6rem',
                fontWeight: 'bold',
                textTransform: 'uppercase',
                letterSpacing: '0.2em'
            }}>
                ⚡ Neural Inversion Control
            </div>
            <div style={{ padding: '1.5rem' }}>
                <p style={{ fontSize: '0.6rem', color: theme.colors.textMuted, marginBottom: '1.5rem', fontStyle: 'italic', lineHeight: 1.6 }}>
                    Manually trigger the STILT-based neural inversion engine for a specific geographic coordinate and date.
                </p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                    {['latitude', 'longitude', 'date'].map(key => (
                        <div key={key}>
                            <label style={labelStyle}>{key}</label>
                            <input
                                type={key === 'date' ? 'date' : 'text'}
                                value={form[key]}
                                onChange={e => setForm({ ...form, [key]: e.target.value })}
                                style={inputStyle}
                                onFocus={e => e.target.style.borderColor = theme.colors.primary}
                                onBlur={e => e.target.style.borderColor = theme.colors.border}
                            />
                        </div>
                    ))}
                </div>

                <button
                    onClick={run}
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '0.75rem',
                        borderRadius: '12px',
                        fontWeight: 'bold',
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.15em',
                        border: 'none',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        background: loading ? '#f3f4f6' : theme.colors.primary,
                        color: loading ? '#9ca3af' : theme.colors.secondary,
                        transition: 'all 0.2s ease'
                    }}
                >
                    {loading ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem' }}>
                            <div className="spinner" style={{ 
                                width: '12px', 
                                height: '12px', 
                                border: '2px solid rgba(255,255,255,0.3)', 
                                borderTop: '2px solid white', 
                                borderRadius: '50%',
                                animation: 'spin 0.8s linear infinite'
                            }} />
                            {processStep === 'AQUIRING_SATELLITE_DATA' ? 'Fetching TROPOMI...' : 'Attributing Source...'}
                        </div>
                    ) : 'Run Inversion'}
                </button>

                {result?.error && (
                    <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '12px' }}>
                        <p style={{ fontSize: '0.6rem', font_weight: 'bold', color: '#991b1b', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Inversion Error</p>
                        <p style={{ fontSize: '0.75rem', color: '#dc2626', margin: 0 }}>{result.error}</p>
                    </div>
                )}

                {result && !result.error && (
                    <div style={{ marginTop: '1.5rem', padding: '1.25rem', background: '#FDF8F3', borderRadius: '12px', border: `1px dashed ${theme.colors.primary}` }}>
                        <p style={{ fontSize: '0.6rem', fontWeight: 'bold', color: theme.colors.primary, textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '0.75rem' }}>Analysis Result</p>
                        <h4 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '0.25rem', margin: 0 }}>{result.top_facility}</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: '0.5rem', marginTop: '1rem', fontSize: '0.7rem' }}>
                            <span style={{ color: theme.colors.textMuted }}>Emission Rate</span>
                            <span style={{ textAlign: 'right', fontWeight: 'bold', color: theme.colors.primary }}>{result.emission_rate_kg_hr?.toLocaleString()} kg/hr</span>
                            
                            <span style={{ color: theme.colors.textMuted }}>Compute Time</span>
                            <span style={{ textAlign: 'right', fontWeight: 'bold', color: theme.colors.primary }}>{result.compute_time_ms} ms</span>
                            
                            <span style={{ color: theme.colors.textMuted }}>Confidence</span>
                            <div style={{ textAlign: 'right' }}>
                                <span style={{ fontWeight: 'bold', color: theme.colors.primary }}>{(result.confidence * 100).toFixed(0)}%</span>
                                <div style={{ width: '100%', height: '4px', background: '#e5e7eb', borderRadius: '2px', marginTop: '4px', overflow: 'hidden' }}>
                                    <div 
                                        style={{ height: '100%', background: '#22c55e', width: `${result.confidence * 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}