// client/src/components/ReportLibrary.jsx
// Shows BOTH pre-generated PDFs (from manifest) and DB-stored custom reports
import { useState, useEffect } from 'react'
import { api } from '../api'
import { theme } from '../design_system'

export default function ReportLibrary() {
    const [manifest, setManifest] = useState(null)
    const [dbReports, setDbReports] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            api.getReportManifest().catch(() => null),
            api.getReportLibrary().catch(() => []),
        ]).then(([m, r]) => {
            setManifest(m)
            setDbReports(r)
        }).finally(() => setLoading(false))
    }, [])

    const triggerDownload = (blob, filename) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
    }

    const handleFacilityDownload = async (fac) => {
        try {
            const blob = await api.downloadFacilityPdf(fac.id)
            triggerDownload(blob, `Fluxara_Facility_${fac.id}.pdf`)
        } catch (e) { alert('Download failed.') }
    }

    const handleRegionDownload = async (region) => {
        try {
            const blob = await api.downloadRegionPdf(region.country)
            triggerDownload(blob, `Fluxara_Region_${region.country}.pdf`)
        } catch (e) { alert('Download failed.') }
    }

    const handleCompanyDownload = async (company) => {
        try {
            const blob = await api.downloadCompanyPdf(company.id)
            triggerDownload(blob, `Fluxara_Company_${company.id}.pdf`)
        } catch (e) { alert('Download failed.') }
    }

    const handleGlobalDownload = async () => {
        try {
            const blob = await api.downloadGlobalPdf()
            triggerDownload(blob, 'Fluxara_Global_Summary.pdf')
        } catch (e) { alert('Download failed.') }
    }

    const handleDbReportDownload = async (report) => {
        try {
            const blob = await api.downloadReport(report.id)
            triggerDownload(blob, `Fluxara_${report.report_type}_${report.id}.pdf`)
        } catch (e) { alert('Download failed.') }
    }

    const formatFileSize = (bytes) => {
        if (!bytes) return '---'
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    }

    if (loading) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: theme.colors.textMuted }}>
                Loading reports...
            </div>
        )
    }

    const hasPreGenerated = manifest && (
        (manifest.facilities?.length > 0) ||
        (manifest.regions?.length > 0) ||
        (manifest.companies?.length > 0) ||
        manifest.global
    )

    if (!hasPreGenerated && dbReports.length === 0) {
        return (
            <div style={{
                background: theme.colors.surface,
                padding: '3rem',
                borderRadius: '16px',
                textAlign: 'center',
                boxShadow: theme.shadows.sm,
                border: `1px solid ${theme.colors.border}`
            }}>
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📄</div>
                <h3 style={{ color: theme.colors.primary, margin: '0 0 0.5rem 0' }}>No Reports Available</h3>
                <p style={{ color: theme.colors.textMuted, margin: 0, fontSize: '0.9rem' }}>
                    Reports are generated automatically and will appear here shortly.
                </p>
            </div>
        )
    }

    const cardStyle = {
        background: 'white',
        padding: '1.25rem',
        borderRadius: '14px',
        border: `1px solid ${theme.colors.border}`,
        boxShadow: theme.shadows.sm,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        transition: 'transform 0.2s, box-shadow 0.2s',
        cursor: 'pointer',
        minHeight: '140px',
    }

    const typeColors = {
        facility: { bg: '#dbeafe', text: '#1e40af', icon: '🏭' },
        region: { bg: '#dcfce7', text: '#166534', icon: '🌍' },
        company: { bg: '#fef3c7', text: '#92400e', icon: '🏢' },
        global: { bg: '#f3e8ff', text: '#7c3aed', icon: '🌐' },
        summary: { bg: '#dcfce7', text: '#166534', icon: '📊' },
        full: { bg: '#dbeafe', text: '#1e40af', icon: '📋' },
        compliance: { bg: '#fef3c7', text: '#92400e', icon: '⚖️' },
    }

    const renderCard = (key, title, subtitle, badge, badgeType, size, onClick) => {
        const colors = typeColors[badgeType] || typeColors.facility
        return (
            <div key={key} style={cardStyle}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = theme.shadows.md; }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = theme.shadows.sm; }}
            >
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '1.5rem' }}>{colors.icon}</span>
                        <span style={{
                            padding: '2px 10px', borderRadius: '12px', fontSize: '0.6rem',
                            fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em',
                            background: colors.bg, color: colors.text
                        }}>{badge}</span>
                    </div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: theme.colors.primary, margin: '0 0 0.25rem 0', lineHeight: '1.3' }}>
                        {title}
                    </h4>
                    <p style={{ fontSize: '0.7rem', color: theme.colors.textMuted, margin: 0 }}>{subtitle}</p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${theme.colors.border}`, paddingTop: '0.75rem', marginTop: '0.75rem' }}>
                    <span style={{ fontSize: '0.7rem', color: theme.colors.textMuted }}>{formatFileSize(size)}</span>
                    <button
                        onClick={(e) => { e.stopPropagation(); onClick(); }}
                        style={{
                            background: theme.colors.primary, color: 'white', border: 'none',
                            padding: '0.35rem 0.9rem', borderRadius: '8px', fontWeight: 'bold',
                            cursor: 'pointer', fontSize: '0.7rem', transition: 'opacity 0.2s'
                        }}
                        onMouseOver={e => e.target.style.opacity = '0.8'}
                        onMouseOut={e => e.target.style.opacity = '1'}
                    >Download PDF</button>
                </div>
            </div>
        )
    }

    return (
        <div>
            {/* Global Report */}
            {manifest?.global && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 'bold', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
                        Global Intelligence Report
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', maxWidth: '400px' }}>
                        {renderCard('global', 'Global Summary Report', `${manifest.global.total_facilities} facilities | ${manifest.global.total_emissions?.toFixed(0)} kg/hr`, 'GLOBAL', 'global', manifest.global.file_size, handleGlobalDownload)}
                    </div>
                </div>
            )}

            {/* Region Reports */}
            {manifest?.regions?.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 'bold', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
                        Regional Reports ({manifest.regions.length})
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                        {manifest.regions.map(r => renderCard(
                            `region-${r.country}`, `${r.country} Regional Summary`, `${r.total_facilities} facilities`,
                            'REGION', 'region', r.file_size, () => handleRegionDownload(r)
                        ))}
                    </div>
                </div>
            )}

            {/* Company Reports */}
            {manifest?.companies?.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 'bold', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
                        Company Reports ({manifest.companies.length})
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                        {manifest.companies.map(c => renderCard(
                            `company-${c.id}`, c.name, `${c.total_facilities} facilities | ${c.total_emissions?.toFixed(0)} kg/hr`,
                            'COMPANY', 'company', c.file_size, () => handleCompanyDownload(c)
                        ))}
                    </div>
                </div>
            )}

            {/* Facility Reports */}
            {manifest?.facilities?.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 'bold', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
                        Facility Reports ({manifest.facilities.length})
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                        {manifest.facilities.map(f => renderCard(
                            `fac-${f.id}`, f.name, `${f.country} | ${f.sector || 'N/A'}`,
                            f.risk_level?.toUpperCase() || 'LOW', 'facility', f.file_size, () => handleFacilityDownload(f)
                        ))}
                    </div>
                </div>
            )}

            {/* DB-Stored Custom Reports */}
            {dbReports.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.8rem', fontWeight: 'bold', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1rem' }}>
                        Custom Reports ({dbReports.length})
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                        {dbReports.map(r => renderCard(
                            `db-${r.id}`, r.title, `${r.region || 'Global'} | ${r.total_facilities || 0} facilities`,
                            r.report_type?.toUpperCase(), r.report_type, r.file_size, () => handleDbReportDownload(r)
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
