// client/src/pages/FacilityDetail.jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { theme } from '../design_system'
import EmissionChart from '../components/emissionchart'

export default function FacilityDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [facility, setFacility] = useState(null)
    const [timeseries, setTimeseries] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const loadDetail = async () => {
            try {
                const fac = await api.getFacility(id);
                setFacility(fac);
                const ts = await api.getTimeseries(id);
                setTimeseries(ts);
            } catch (e) {
                console.error("Detail fetch failed:", e);
            } finally {
                setLoading(false);
            }
        };
        loadDetail();
    }, [id])

    if (loading) return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', fontFamily: 'serif' }}>
            <div className="skeleton" style={{ width: '100px', height: '20px', marginBottom: '2rem' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3rem' }}>
                <div>
                    <div className="skeleton" style={{ width: '300px', height: '40px', marginBottom: '1rem' }} />
                    <div className="skeleton" style={{ width: '200px', height: '20px' }} />
                </div>
                <div className="skeleton" style={{ width: '150px', height: '30px', borderRadius: '15px' }} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', marginBottom: '3rem' }}>
                <div className="skeleton" style={{ height: '120px', borderRadius: '16px' }} />
                <div className="skeleton" style={{ height: '120px', borderRadius: '16px' }} />
                <div className="skeleton" style={{ height: '120px', borderRadius: '16px' }} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                <div className="skeleton" style={{ height: '300px', borderRadius: '16px' }} />
                <div className="skeleton" style={{ height: '300px', borderRadius: '16px' }} />
            </div>
        </div>
    )

    if (!facility) return (
        <div style={{ padding: '4rem', textAlign: 'center', fontFamily: 'serif' }}>
            <h2 style={{ color: theme.colors.primary }}>Site Not Found</h2>
            <p style={{ color: theme.colors.textMuted }}>The requested facility ID does not exist in the Fluxara Intelligence Registry.</p>
            <button onClick={() => navigate('/facilities')} style={{ marginTop: '1rem', background: theme.colors.primary, color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer' }}>Return to Directory</button>
        </div>
    )


    const cardStyle = {
        background: 'white',
        padding: '1.5rem',
        borderRadius: '16px',
        border: `1px solid ${theme.colors.border}`,
        boxShadow: theme.shadows.sm
    }

    const labelStyle = {
        fontSize: '0.65rem',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        color: theme.colors.textMuted,
        marginBottom: '0.5rem',
        display: 'block'
    }

    const downloadPDF = async () => {
        try {
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${baseUrl}/reports/facility/${id}/pdf`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Fluxara_Audit_${facility.name}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error("PDF download failed:", e);
        }
    }

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', fontFamily: 'serif' }}>
            <button 
                onClick={() => navigate(-1)}
                style={{ background: 'none', border: 'none', color: theme.colors.primary, fontWeight: 'bold', cursor: 'pointer', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
                ← Back to Intelligence
            </button>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3rem' }}>
                <div>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: theme.colors.primary, margin: 0 }}>{facility.name}</h1>
                    <p style={{ fontSize: '1rem', color: theme.colors.textMuted, marginTop: '0.5rem', margin: 0 }}>
                        {facility.state}, {facility.country} · {facility.lat?.toFixed(4) || '0.0000'}, {facility.lon?.toFixed(4) || '0.0000'}
                    </p>
                </div>
                <div style={{ textAlign: 'right', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button 
                        onClick={downloadPDF}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '12px',
                            background: theme.colors.secondary,
                            color: theme.colors.primary,
                            border: `1px solid ${theme.colors.primary}`,
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => { e.target.style.background = theme.colors.primary; e.target.style.color = theme.colors.secondary; }}
                        onMouseOut={(e) => { e.target.style.background = theme.colors.secondary; e.target.style.color = theme.colors.primary; }}
                    >
                        Export PDF Audit
                    </button>
                    <span style={{
                        padding: '6px 16px',
                        borderRadius: '24px',
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        background: facility.risk_level === 'high' ? '#fee2e2' : '#dcfce7',
                        color: facility.risk_level === 'high' ? '#991b1b' : '#166534'
                    }}>
                        Status: {facility.risk_level === 'high' ? 'Alert Active' : 'Normal Operations'}
                    </span>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
                <div style={cardStyle}>
                    <span style={labelStyle}>EPA Baseline</span>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: theme.colors.primary, margin: 0 }}>{facility.epa_reported || '0'} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', opacity: 0.6 }}>kg/hr</span></p>
                    <p style={{ fontSize: '0.75rem', color: theme.colors.textMuted, marginTop: '0.5rem', margin: 0 }}>Last reported via GHGRP 2023</p>
                </div>
                <div style={{ ...cardStyle, background: theme.colors.primary, color: 'white' }}>
                    <span style={{ ...labelStyle, color: theme.colors.accent }}>Fluxara Latest</span>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>{facility.fluxara_latest ?? 'No data'} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', opacity: 0.6 }}>kg/hr</span></p>
                    <p style={{ fontSize: '0.75rem', color: theme.colors.accent, marginTop: '0.5rem', margin: 0 }}>Calculated via TROPOMI {new Date().toLocaleDateString()}</p>
                </div>
                <div style={cardStyle}>
                    <span style={labelStyle}>Satellite Confidence</span>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: theme.colors.primary, margin: 0 }}>94.1%</p>
                    <div style={{ width: '100%', height: '4px', background: '#f3f4f6', borderRadius: '2px', marginTop: '1rem', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: '#3D0C14', width: '94.1%' }} />
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                {timeseries && <EmissionChart data={timeseries} />}
                <div style={cardStyle}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '1.5rem', margin: 0 }}>Asset Metadata</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                        <div>
                            <span style={{ fontSize: '0.65rem', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Basin</span>
                            <p style={{ fontSize: '0.9rem', color: theme.colors.primary, fontWeight: 'bold', margin: 0 }}>Permian - Delaware</p>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.65rem', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Operator ID</span>
                            <p style={{ fontSize: '0.9rem', color: theme.colors.primary, fontWeight: 'bold', margin: 0 }}>{facility.id.toString().padStart(8, '0')}</p>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.65rem', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Reporting Tier</span>
                            <p style={{ fontSize: '0.9rem', color: theme.colors.primary, fontWeight: 'bold', margin: 0 }}>Subpart W - Tier 2</p>
                        </div>
                    </div>
                    <button style={{
                        width: '100%',
                        marginTop: '2rem',
                        padding: '1rem',
                        background: '#f3f4f6',
                        color: theme.colors.primary,
                        borderRadius: '12px',
                        border: 'none',
                        fontWeight: 'bold',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                    }}>
                        Request Raw Telemetry
                    </button>
                </div>
            </div>
        </div>
    )
}