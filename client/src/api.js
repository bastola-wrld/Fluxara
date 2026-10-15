// client/src/api.js
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getHeaders = () => {
    const token = localStorage.getItem('token');
    const h = { 'Content-Type': 'application/json' };
    if (token) {
        h['Authorization'] = `Bearer ${token}`;
    }
    return h;
};

const getOptions = () => ({ headers: getHeaders(), cache: 'no-store' });

export const api = {
    login: (email, password) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        return fetch(`${BASE}/auth/login`, {
            method: 'POST',
            body: formData
        }).then(async r => {
            if (r.ok) return r.json();
            const err = await r.json().catch(() => ({}));
            return Promise.reject(err);
        });
    },

    getFacilities: () => fetch(`${BASE}/v1/facilities`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacility: (id) => fetch(`${BASE}/v1/facilities/${id}`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacilityInversions: (id) => fetch(`${BASE}/v1/facilities/${id}/inversions`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacilityAlerts: (id) => fetch(`${BASE}/v1/facilities/${id}/alerts`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    getAlerts: (resolved = false) => fetch(`${BASE}/v1/alerts?resolved=${resolved}`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    getAlertCount: () => fetch(`${BASE}/v1/alerts/count`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    resolveAlert: (id) => fetch(`${BASE}/v1/alerts/${id}/resolve`, { method: 'PATCH', headers: getHeaders() }).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    getReports: () => fetch(`${BASE}/v1/reports`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    getReport: (id) => fetch(`${BASE}/v1/reports/${id}`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),

    // On-Demand PDF Generation (admin custom reports -> DB)
    generateAdminReport: (body) => fetch(`${BASE}/v1/reports/generate`, {
        method: 'POST', headers: getHeaders(), body: JSON.stringify(body)
    }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getReportLibrary: () => fetch(`${BASE}/v1/reports/library`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    downloadReport: (id) => fetch(`${BASE}/v1/reports/download/${id}`, {
        headers: getHeaders()
    }).then(r => r.ok ? r.blob() : Promise.reject(r)),
    deleteGeneratedReport: (id) => fetch(`${BASE}/v1/reports/generated/${id}`, {
        method: 'DELETE', headers: getHeaders()
    }).then(r => r.ok ? r.json() : Promise.reject(r)),

    // Pre-Generated PDF Downloads (instant from disk)
    getReportManifest: () => fetch(`${BASE}/v1/reports/manifest`, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r)),
    downloadFacilityPdf: (id) => fetch(`${BASE}/v1/reports/download/facility/${id}`, {
        headers: getHeaders()
    }).then(r => r.ok ? r.blob() : Promise.reject(r)),
    downloadRegionPdf: (country) => fetch(`${BASE}/v1/reports/download/region/${country}`, {
        headers: getHeaders()
    }).then(r => r.ok ? r.blob() : Promise.reject(r)),
    downloadCompanyPdf: (orgId) => fetch(`${BASE}/v1/reports/download/company/${orgId}`, {
        headers: getHeaders()
    }).then(r => r.ok ? r.blob() : Promise.reject(r)),
    downloadGlobalPdf: () => fetch(`${BASE}/v1/reports/download/global`, {
        headers: getHeaders()
    }).then(r => r.ok ? r.blob() : Promise.reject(r)),
    triggerRegeneration: () => fetch(`${BASE}/v1/reports/regenerate`, {
        method: 'POST', headers: getHeaders()
    }).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    getTimeseries: (facilityId = null) => {
        const url = facilityId ? `${BASE}/v1/timeseries?facility_id=${facilityId}` : `${BASE}/v1/timeseries`;
        return fetch(url, getOptions()).then(r => r.ok ? r.json() : Promise.reject(r));
    },

    runInversion: (body) => fetch(`${BASE}/v1/invert`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body)
    }).then(r => r.ok ? r.json() : Promise.reject(r)),

    // Admin API
    getAdminOverview: () => fetch(`${BASE}/admin/overview`, getOptions()).then(r => r.json()),
    getAdminOrganisations: () => fetch(`${BASE}/admin/organisations`, getOptions()).then(r => r.json()),
    createOrganisation: (body) => fetch(`${BASE}/admin/organisations`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),
    disableOrganisation: (id) => fetch(`${BASE}/admin/organisations/${id}`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    hardDeleteOrganisation: (id) => fetch(`${BASE}/admin/organisations/${id}/hard`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    getAdminUsers: () => fetch(`${BASE}/admin/users`, getOptions()).then(r => r.json()),
    createUser: (body) => fetch(`${BASE}/admin/users`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),
    changeUserRole: (id, role) => fetch(`${BASE}/admin/users/${id}/role/${role}`, { method: 'PATCH', headers: getHeaders() }).then(r => r.json()),
    disableUser: (id) => fetch(`${BASE}/admin/users/${id}`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    hardDeleteUser: (id) => fetch(`${BASE}/admin/users/${id}/hard`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    getAdminInversions: () => fetch(`${BASE}/admin/inversions`, getOptions()).then(r => r.json()),
    createAdminInversion: (body) => fetch(`${BASE}/admin/inversions`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),
    deleteAdminInversion: (id) => fetch(`${BASE}/admin/inversions/${id}`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    getAdminAlerts: () => fetch(`${BASE}/admin/alerts`, getOptions()).then(r => r.json()),
    createAdminAlert: (body) => fetch(`${BASE}/admin/alerts`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),
    deleteAdminAlert: (id) => fetch(`${BASE}/admin/alerts/${id}`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),

    // Company API
    getCompanyOverview: (orgId) => fetch(`${BASE}/company/overview/${orgId}`, getOptions()).then(r => r.json()),
    getCompanyFacilities: (orgId) => fetch(`${BASE}/company/facilities/${orgId}`, getOptions()).then(r => r.json()),
    addFacility: (orgId, body) => fetch(`${BASE}/company/facilities/${orgId}`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),
    removeFacility: (id) => fetch(`${BASE}/company/facilities/${id}`, { method: 'DELETE', headers: getHeaders() }).then(r => r.json()),
    getCompanyInversions: (orgId) => fetch(`${BASE}/company/inversions/${orgId}`, { headers: getHeaders() }).then(r => r.json()),
    getCompanyAlerts: (orgId) => fetch(`${BASE}/company/alerts/${orgId}`, { headers: getHeaders() }).then(r => r.json()),
    resolveCompanyAlert: (id) => fetch(`${BASE}/company/alerts/${id}/resolve`, { method: 'PATCH', headers: getHeaders() }).then(r => r.json()),
    getCompanyReports: (orgId) => fetch(`${BASE}/company/reports/${orgId}`, { headers: getHeaders() }).then(r => r.json()),
    generateReport: (orgId, body) => fetch(`${BASE}/company/reports/${orgId}/generate`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) }).then(r => r.json()),

    // Government API
    getGovOverview: (country, sector) => {
        let url = `${BASE}/government/overview?`;
        if (country) url += `country=${country}&`;
        if (sector) url += `sector=${sector}&`;
        return fetch(url, { headers: getHeaders() }).then(r => r.json());
    },
    getGovFacilities: (country, sector) => {
        let url = `${BASE}/government/facilities?`;
        if (country) url += `country=${country}&`;
        if (sector) url += `sector=${sector}&`;
        return fetch(url, { headers: getHeaders() }).then(r => r.json());
    },
    getUnderreporting: (threshold, country, sector) => {
        let url = `${BASE}/government/underreporting?threshold=${threshold}&`;
        if (country) url += `country=${country}&`;
        if (sector) url += `sector=${sector}&`;
        return fetch(url, { headers: getHeaders() }).then(r => r.json());
    },
    getNDCVerification: (country) => fetch(`${BASE}/government/ndc-verification?country=${country}`, { headers: getHeaders() }).then(r => r.json()),
    getGovSectors: (country) => {
        let url = `${BASE}/government/sectors?`;
        if (country) url += `country=${country}`;
        return fetch(url, { headers: getHeaders() }).then(r => r.json());
    },
};
