import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { theme } from '../design_system'
import { api } from '../api'

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const navigate = useNavigate()

    const handleLogin = async (e) => {
        e.preventDefault()
        setError('')
        try {
            const data = await api.login(email, password)
            localStorage.setItem("token", data.access_token)
            localStorage.setItem("role", data.role)
            localStorage.setItem("userEmail", data.email)
            localStorage.setItem("orgId", data.org_id || '')

            if (data.role === "admin") {
                navigate("/admin")
            } else if (data.role === "company") {
                navigate(`/company/${data.org_id}`)
            } else if (data.role === "government") {
                navigate("/government")
            } else {
                navigate("/")
            }
            window.location.reload()
        } catch (err) {
            let msg = "Invalid credentials. Please try again.";
            if (err.detail) msg = err.detail;
            else if (err.message) msg = err.message;
            setError(msg);
        }
    }

    return (
        <div style={{ 
            height: '100vh', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            background: theme.colors.primary,
            fontFamily: 'serif'
        }}>
            <div style={{ 
                background: theme.colors.surface, 
                padding: '3rem', 
                borderRadius: theme.radius.lg, 
                boxShadow: theme.shadows.lg,
                width: '100%',
                maxWidth: '400px',
                textAlign: 'center'
            }}>
                <h1 style={{ color: theme.colors.primary, fontSize: '2.5rem', marginBottom: '0.5rem', letterSpacing: '-2px' }}>FLUXARA</h1>
                <p style={{ color: theme.colors.textMuted, fontSize: '0.9rem', marginBottom: '2rem' }}>Source-attributed intelligence portal</p>
                
                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {error && <div style={{ color: '#ef4444', fontSize: '0.8rem', marginBottom: '0.5rem' }}>{error}</div>}
                    
                    <div style={{ textAlign: 'left' }}>
                        <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.colors.textMuted, display: 'block', marginBottom: '0.5rem' }}>EMAIL ADDRESS</label>
                        <input 
                            type="email" 
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="name@company.com"
                            style={{ 
                                width: '100%', 
                                padding: '0.75rem', 
                                borderRadius: theme.radius.sm, 
                                border: `1px solid ${theme.colors.border}`,
                                outline: 'none'
                            }} 
                        />
                    </div>
                    
                    <div style={{ textAlign: 'left' }}>
                        <label style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.colors.textMuted, display: 'block', marginBottom: '0.5rem' }}>PASSWORD</label>
                        <input 
                            type="password" 
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            style={{ 
                                width: '100%', 
                                padding: '0.75rem', 
                                borderRadius: theme.radius.sm, 
                                border: `1px solid ${theme.colors.border}`,
                                outline: 'none'
                            }} 
                        />
                    </div>

                    <button 
                        type="submit"
                        style={{ 
                            background: theme.colors.primary, 
                            color: theme.colors.secondary, 
                            padding: '1rem', 
                            borderRadius: theme.radius.sm, 
                            border: 'none', 
                            fontWeight: 'bold', 
                            cursor: 'pointer',
                            marginTop: '1rem',
                            transition: 'opacity 0.2s'
                        }}
                        onMouseOver={(e) => e.target.style.opacity = 0.9}
                        onMouseOut={(e) => e.target.style.opacity = 1}
                    >
                        ENTER PORTAL
                    </button>
                </form>
                
                <div style={{ marginTop: '2rem', fontSize: '0.7rem', color: theme.colors.textMuted, opacity: 0.6 }}>
                    SECURE ENCRYPTED UPLINK · ESA TROPOMI DATA
                </div>
            </div>
        </div>
    )
}
