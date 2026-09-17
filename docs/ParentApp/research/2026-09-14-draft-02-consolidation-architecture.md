---
project: ForKhatri
title: Platform Consolidation — Unified Identity Architecture Design
date: 2026-09-14
status: Superseded
scope: All modules (Vyapar, Milavn, Mangaly, Counsel, Dashboard, Payment Services, Loans & Finance)
approver: Chief Architect (Krishna Kategaru)
---

> **Superseded draft.** Kept for history. Decisions and corrections: ../00c-identity-and-entrance-decisions.md. Contract: ../07-tech-reqs.md.

# Platform Consolidation: Unified Identity + Modular Frontend Architecture

This document specifies **exactly how** to implement your vision: "One ForKhatri app. One user. Modules discovered and navigated from a dashboard."

It combines three proven architectural patterns (drawn from Slack, GitHub, Shopify 2026 implementations) and tailors them for ForKhatri's specific constraints.

---

## Quick Summary: The Three Patterns

| Pattern | Purpose | Real-World Example | Recommendation |
|---------|---------|-------------------|-----------------|
| **Pattern 1: Unified Identity + Per-Module Tables** | One user exists globally; each module tracks that user's tier/role independently | Slack (global user + per-workspace member), GitHub (global user + per-org member) | ✅ **ADOPT** |
| **Pattern 2: Module Federation Frontend** | Separate React apps deployed independently, loaded dynamically by platform shell | Shopify Admin, Figma plugins, Figma teams | ✅ **ADOPT** |
| **Pattern 3: Hybrid JWT Authorization** | JWT carries tier/role claims for fast UI decisions; API always re-validates in database | Auth0 + Hasura, Firebase + Firestore, SuperTokens 2026 standard | ✅ **ADOPT** |

---

## Pattern 1: Unified User Identity + Per-Module User Tables

### Data Model

```
┌─────────────────────────────────────────────────────────────┐
│ IDENTITY & TRUST SERVICE (IdentityDB - Postgres)           │
├─────────────────────────────────────────────────────────────┤
│ platform_user                                               │
│ ├─ user_id (PK)                                            │
│ ├─ phone_number (unique, login key)                        │
│ ├─ email (optional)                                        │
│ ├─ name                                                    │
│ ├─ created_at                                              │
│ └─ last_login_at                                           │
│                                                             │
│ credential                                                  │
│ ├─ credential_id (PK)                                      │
│ ├─ user_id (FK → platform_user)                            │
│ ├─ otp_hash                                                │
│ ├─ otp_expires_at                                          │
│ └─ verified_at                                             │
│                                                             │
│ verified_credential (shared across Vyapar/Counsel)         │
│ ├─ credential_id (PK)                                      │
│ ├─ user_id (FK → platform_user)                            │
│ ├─ credential_type (e.g., 'pan', 'gst', 'license')        │
│ ├─ credential_value (masked)                               │
│ ├─ verified_by (e.g., 'pan_provider', 'gst_provider')     │
│ ├─ verification_result (pass/fail)                         │
│ └─ verified_at                                             │
│                                                             │
│ member_reputation                                          │
│ ├─ reputation_id (PK)                                      │
│ ├─ user_id (FK → platform_user)                            │
│ ├─ module_context (e.g., 'vyapar', 'mangaly', 'milavn')   │
│ ├─ trust_score (0-100, computed per context)              │
│ ├─ feedback_count                                          │
│ └─ last_updated_at                                         │
└─────────────────────────────────────────────────────────────┘
        ↑ ONE source of truth for all users
        │
        ├──────────────────┬──────────────┬──────────────┐
        │                  │              │              │
```

```
┌──────────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│ MANGALY SERVICE (MangalyDB)  │  │ VYAPAR (Core Platform)   │  │ MILAVN (Core Platform)   │
├──────────────────────────────┤  ├──────────────────────────┤  ├──────────────────────────┤
│ mangaly_matrimonial_member   │  │ vyapar_professional_prof │  │ milavn_organizer_profile │
│ ├─ member_id (PK)            │  │ ├─ profile_id (PK)       │  │ ├─ organizer_id (PK)    │
│ ├─ user_id (FK→IdentityDB)   │  │ ├─ user_id (FK→Identity) │  │ ├─ user_id (FK→Identity)│
│ ├─ tier ('free','premium')   │  │ ├─ tier ('basic','pro')  │  │ ├─ tier ('creator',...)  │
│ ├─ verification_status       │  │ ├─ business_name         │  │ ├─ circle_count          │
│ ├─ profile_data              │  │ ├─ license_number        │  │ ├─ event_count           │
│ ├─ photos (FK→ObjStore)      │  │ ├─ verified_by (ext API) │  │ ├─ member_count          │
│ └─ ... matrimonial fields... │  │ └─ ... professional ...  │  │ └─ ... organizer ...     │
│                              │  │                          │  │                          │
│ mangaly_matches              │  │ vyapar_opportunity       │  │ milavn_event             │
│ ├─ match_id                  │  │ ├─ opportunity_id        │  │ ├─ event_id              │
│ ├─ user_id (FK→IdentityDB)   │  │ ├─ user_id (FK→Identity) │  │ ├─ user_id (FK→Identity) │
│ └─ ...                       │  │ └─ ...                   │  │ └─ ...                   │
│                              │  │                          │  │                          │
│ mangaly_circle               │  │                          │  │                          │
│ ├─ circle_id                 │  │                          │  │                          │
│ ├─ admin_user_id (FK→Identity)                             │  │                          │
│ └─ ...                       │  │                          │  │                          │
└──────────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
     Tier: Free/Premium/Elite         Tier: Basic/Pro/Elite        Tier: Creator/Pro/Elite
     No role inheritance              No role inheritance          No role inheritance
     from other modules               from other modules           from other modules
```

### Key Principles

**1. One Unified Source of Truth**
- `platform_user` table in Identity & Trust Service is the ONLY place a user is created
- Every module references `user_id` as foreign key
- No module duplicates or owns the user record

**2. No Role Inheritance Across Modules**
- User's tier in Vyapar is INDEPENDENT of tier in Mangaly
- Example: User can be "Pro" in Vyapar (verified business) but "Free" in Mangaly (new matrimonial profile)
- Each module manages its own tier enum, permissions, and validation logic
- No shared tier table; each module has its own `tier` column

**3. Per-Module Reputation (Context-Aware Trust)**
- `member_reputation` table has `module_context` column
- User's trust score is computed per context: "professional context" vs "matrimonial context"
- Same user can have high trust in Vyapar, low trust in Mangaly
- Aligns with sealed PRODUCT-GUARDRAILS.md: "a person trusted professionally is not automatically trusted matrimonially"

**4. Module Access Discovery**
Two options (pick one):

**Option A: Lightweight Junction Table** (recommended for clarity)
```sql
CREATE TABLE platform.user_module_access (
  access_id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES identity_db.platform_user(user_id),
  module_key VARCHAR NOT NULL,  -- 'vyapar', 'mangaly', 'milavn', etc.
  tier VARCHAR,                  -- 'free', 'premium', 'elite' (denormalized for speed)
  has_verified_credentials BOOLEAN,  -- cached from verified_credential table
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(user_id, module_key)
);
```
- Shell queries this table to know which module tiles to show user
- Tier/access info is denormalized here for speed (no N+1 queries)
- Updated whenever user's tier changes in any module

**Option B: No Junction Table, Query Each Module** (simpler, slower)
- Shell makes requests to each module: `GET /modules/<module>/user-access?user_id=X`
- Module returns: `{ has_access: true, tier: 'premium' }`
- Slower (N module requests), but simpler setup
- Recommended only if < 5 modules

**Recommendation for ForKhatri:** Use Option A (junction table). You'll have 7 modules by V3, so denormalization pays off.

---

## Pattern 2: Module Federation Frontend (Separate Apps, Unified Shell)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FORKHATRI SHELL (forkhathri.app:3000)                                      │
│ Host app – owns top-level navigation, layout, theme, auth context         │
│                                                                             │
│ ┌──────────────────────────────────────────────────────────────────────┐  │
│ │ Header (Theme switcher, profile, notifications, module menu)       │  │
│ ├──────────────────────────────────────────────────────────────────────┤  │
│ │ Dashboard / Module Tiles                                            │  │
│ │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│ │  │ Vyapar Pro  │  │ Mangaly Pro  │  │ Milavn PRO   │              │  │
│ │  │ (Pro tier)  │  │ (Elite tier) │  │ (Creator)    │              │  │
│ │  └─────────────┘  └──────────────┘  └──────────────┘              │  │
│ │                                                                     │  │
│ ├──────────────────────────────────────────────────────────────────────┤  │
│ │ Dynamic Module Container                                           │  │
│ │                                                                     │  │
│ │  ┌──────────────────────────────────────────────────────────┐     │  │
│ │  │ Currently loaded: Vyapar Module                          │     │  │
│ │  │ (Rendered by Module Federation remote)                 │     │  │
│ │  └──────────────────────────────────────────────────────────┘     │  │
│ │                                                                     │  │
│ │  (When user clicks "Mangaly" tile: Vyapar unloads, Mangaly loads) │  │
│ │                                                                     │  │
│ └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ Shared Scope (negotiated at runtime):                                     │
│ ├─ React 18 (singleton)                                                   │
│ ├─ TailwindCSS (singleton)                                                │
│ ├─ @forkhatri/auth-context (JWT, user identity, tier)                    │
│ ├─ @forkhatri/api-client (base URL, error handling, JWT injection)        │
│ └─ @forkhatri/design-tokens (colors, typography, spacing)                │
└─────────────────────────────────────────────────────────────────────────────┘
    ↑                  ↑                   ↑                      ↑
    │                  │                   │                      │
    │ Module           │ Module            │ Module               │ Shared
    │ Federation       │ Federation        │ Federation           │ Services
    │ remote           │ remote            │ remote               │
    │                  │                   │                      │
┌───┴──┐         ┌─────┴──┐          ┌────┴───┐          ┌────────┴─────┐
│VYAPAR│         │MANGALY │          │MILAVN  │          │ API GATEWAY  │
│3001  │         │3002    │          │3003    │          │ 8000         │
│      │         │        │          │        │          │              │
│Next  │         │Next    │          │Next    │          │ Routes to:   │
│.js   │         │.js     │          │.js     │          │ ├─ Vyapar    │
│SPA   │         │SPA     │          │SPA     │          │ ├─ Mangaly   │
│      │         │        │          │        │          │ ├─ Milavn    │
│Module│         │Module  │          │Module  │          │ └─ Identity  │
│Fed.  │         │Fed.    │          │Fed.    │          │              │
│      │         │        │          │        │          │ Enforces:    │
│Remote│         │Remote  │          │Remote  │          │ ├─ JWT valid │
│Entry │         │Entry   │          │Entry   │          │ ├─ Module    │
│      │         │        │          │        │          │ │  access    │
└──────┘         └────────┘          └────────┘          │ └─ Tier      │
                                                          │    validation│
                                                          └──────────────┘
```

### Implementation: Module Federation Setup

**Shell (forkhatri-shell) Configuration:**

```javascript
// next.config.js (shell)
const NextFederationPlugin = require('@module-federation/nextjs-mf');

module.exports = {
  webpack: (config, options) => {
    config.plugins.push(
      new NextFederationPlugin({
        name: 'forkhatri_shell',
        filename: 'static/chunks/remoteEntry.js',
        
        // This shell exposes shared utilities to modules
        exposes: {
          './auth-context': './src/context/AuthContext.tsx',
          './api-client': './src/lib/apiClient.ts',
          './design-tokens': './src/styles/tokens.ts',
        },
        
        // This shell consumes each module's remote entry
        remotes: {
          vyapar: 'vyapar@http://localhost:3001/_next/static/chunks/remoteEntry.js',
          mangaly: 'mangaly@http://localhost:3002/_next/static/chunks/remoteEntry.js',
          milavn: 'milavn@http://localhost:3003/_next/static/chunks/remoteEntry.js',
        },
        
        // Shared dependencies (negotiated at runtime)
        shared: {
          react: { singleton: true, requiredVersion: '^18' },
          'react-dom': { singleton: true, requiredVersion: '^18' },
          'next/router': { singleton: true },
          '@forkhatri/design-tokens': { singleton: true },
        },
      })
    );
    return config;
  },
};
```

**Each Module (vyapar, mangaly, milavn) Configuration:**

```javascript
// next.config.js (module)
const NextFederationPlugin = require('@module-federation/nextjs-mf');

module.exports = {
  webpack: (config, options) => {
    config.plugins.push(
      new NextFederationPlugin({
        name: 'vyapar',  // change to 'mangaly', 'milavn' for other modules
        filename: 'static/chunks/remoteEntry.js',
        
        // This module exposes its main page component
        exposes: {
          './ModuleApp': './src/ModuleApp.tsx',
          './pages': './src/pages',
        },
        
        // This module consumes shell's utilities
        remotes: {
          shell: 'forkhatri_shell@http://localhost:3000/_next/static/chunks/remoteEntry.js',
        },
        
        shared: {
          react: { singleton: true, requiredVersion: '^18' },
          'react-dom': { singleton: true, requiredVersion: '^18' },
          '@forkhatri/design-tokens': { singleton: true },
        },
      })
    );
    return config;
  },
};
```

**Shell Dynamic Loader (pages/[module]/index.tsx):**

```typescript
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useAuth } from '@/context/AuthContext';

const moduleComponents: Record<string, () => Promise<any>> = {
  vyapar: () => import('vyapar/ModuleApp'),
  mangaly: () => import('mangaly/ModuleApp'),
  milavn: () => import('milavn/ModuleApp'),
};

export default function ModulePage() {
  const router = useRouter();
  const { user, userTier } = useAuth();
  const moduleName = router.query.module as string;
  
  if (!moduleName || !moduleComponents[moduleName]) {
    return <div>Module not found</div>;
  }
  
  // Dynamic import of the module
  const ModuleComponent = dynamic(
    () => moduleComponents[moduleName](),
    { loading: () => <div>Loading...</div> }
  );
  
  return (
    <div>
      {/* Module renders here */}
      <ModuleComponent />
    </div>
  );
}
```

### Key Benefits of Module Federation

✅ **Independent Deployment**: Vyapar deploys to 3001 without restarting shell (3000) or other modules  
✅ **No Re-Login on Module Switch**: User switches from Vyapar → Mangaly without re-login, same JWT  
✅ **Zero Downtime Updates**: One module can be updated while others remain live  
✅ **Shared Dependencies**: React/TailwindCSS loaded once (Webpack singleton), not duplicated  
✅ **Per-Module Bundle Size**: Each module only loads when user navigates to it  
✅ **Loose Coupling**: Modules know only about shared interfaces, not each other's internals  

### Deployment Topology

```
Development (localhost):
├─ forkhatri.app:3000 (shell, dev server)
├─ vyapar.forkhatri.app:3001 (module, dev server)
├─ mangaly.forkhatri.app:3002 (module, dev server)
├─ milavn.forkhatri.app:3003 (module, dev server)
└─ api.forkhatri.app:8000 (API gateway)

Production (Kubernetes):
├─ forkhatri.app (shell container)
├─ vyapar.forkhatri.app (module container, auto-scaled)
├─ mangaly.forkhatri.app (module container, auto-scaled)
├─ milavn.forkhatri.app (module container, auto-scaled)
├─ api.forkhatri.app (API gateway, auto-scaled)
└─ Postgres instances (per ARCHITECTURE.md)
```

Each module container serves its own Next.js app with remoteEntry.js.  
Shell makes HTTP requests to fetch remoteEntry.js from each module.  
DNS/routing ensures vyapar.forkhatri.app → Vyapar container, etc.

---

## Pattern 3: Hybrid JWT Authorization Flow

### Token Structure

```json
{
  "sub": "user-12345",
  "email": "krishna@forkhatri.app",
  "phone": "+91-9999-999999",
  "iat": 1726322400,
  "exp": 1726326000,
  "aud": "forkhatri-platform",
  
  // Per-module tiers (embedded for fast UI decisions)
  "tiers": {
    "vyapar": "pro",
    "mangaly": "elite",
    "milavn": "creator"
  },
  
  // Per-module roles (if applicable)
  "roles": {
    "mangaly": ["member"],
    "milavn": ["organizer"],
    "vyapar": ["professional"]
  },
  
  // Modules this user has access to
  "modules": ["vyapar", "mangaly", "milavn"],
  
  // Verification flags
  "verified_credentials": {
    "pan": true,
    "gst": false,
    "professional_license": false
  },
  
  // Standard JWT claims for refresh/rotation
  "type": "access_token",
  "jti": "unique-token-id-for-revocation"
}
```

### Complete Login Flow

```
1. USER VISITS FORKHATHRI
   ┌──────────────────────────────────────────┐
   │ User navigates to forkhatri.app/login    │
   └──────────────────────────────────────────┘
   ↓

2. SHELL SHOWS LOGIN SCREEN
   ┌──────────────────────────────────────────┐
   │ Enter phone number → "Send OTP"          │
   └──────────────────────────────────────────┘
   ↓

3. SHELL CALLS IDENTITY SERVICE
   POST /auth/send-otp
   {
     "phone": "+91-9999-999999"
   }
   ↓

4. IDENTITY SERVICE SENDS OTP (SMS)
   ┌──────────────────────────────────────────┐
   │ OTP: 123456 sent to user's phone         │
   └──────────────────────────────────────────┘
   ↓

5. USER ENTERS OTP
   ┌──────────────────────────────────────────┐
   │ Enter OTP: 123456 → "Verify"             │
   └──────────────────────────────────────────┘
   ↓

6. SHELL CALLS IDENTITY SERVICE
   POST /auth/verify-otp
   {
     "phone": "+91-9999-999999",
     "otp": "123456"
   }
   ↓

7. IDENTITY SERVICE RESPONDS (if valid OTP)
   200 OK
   {
     "access_token": "eyJhbGc...(JWT as shown above)",
     "refresh_token": "refresh_token_value",
     "token_type": "Bearer",
     "expires_in": 3600
   }
   ↓

8. SHELL STORES TOKENS
   - access_token → localStorage (can be read by JS)
   - refresh_token → httpOnly cookie (only sent by browser)
   ↓

9. SHELL DECODES JWT & RENDERS DASHBOARD
   ┌──────────────────────────────────────────┐
   │ Read JWT claims:                         │
   │ - tiers: { vyapar: 'pro', ... }          │
   │ - modules: ['vyapar', 'mangaly', ...]    │
   │ - Render module tiles for accessible     │
   │   modules                                │
   └──────────────────────────────────────────┘
   ↓

10. USER CLICKS "MANGALY" TILE
    ┌──────────────────────────────────────────┐
    │ Shell loads Mangaly module via Module    │
    │ Federation, passes JWT via context       │
    └──────────────────────────────────────────┘
    ↓

11. MANGALY LOADS & READS JWT
    ┌──────────────────────────────────────────┐
    │ Mangaly component:                       │
    │ - Reads JWT from AuthContext             │
    │ - Checks tier: "elite" → show premium    │
    │   features in UI                         │
    │ - User sees Mangaly interface            │
    └──────────────────────────────────────────┘
    ↓

12. USER TAKES ACTION IN MANGALY (e.g., view profile)
    GET /mangaly/api/profile
    Headers: Authorization: Bearer eyJhbGc...
    ↓

13. MANGALY API VALIDATES JWT & RE-VALIDATES TIER
    ✓ Verify JWT signature (using public key from Identity)
    ✓ Check token expiry
    ✓ Extract user_id from JWT
    ✓ Query mangaly_matrimonial_member table:
      - Is user_id present?
      - What is their tier?
    ✓ If tier != JWT claim (tier changed mid-session),
      use DATABASE VALUE (more recent)
    ✓ Check: Can this tier see this profile?
    ✓ Return profile data
    ↓

14. RESPONSE TO MANGALY FRONTEND
    200 OK
    {
      "profile": { ... }
    }
    ↓

15. USER SWITCHES TO VYAPAR
    Click "Vyapar" tile in module menu
    ┌──────────────────────────────────────────┐
    │ Shell unmounts Mangaly, loads Vyapar     │
    │ Same JWT still valid (not expired)       │
    │ No re-login!                             │
    └──────────────────────────────────────────┘
    ↓

16. TOKEN EXPIRES (after 1 hour)
    Access token in localStorage is stale
    User makes API call:
    GET /vyapar/api/opportunities
    ↓

17. API REJECTS EXPIRED TOKEN
    401 Unauthorized
    {
      "error": "token_expired",
      "message": "Please refresh your token"
    }
    ↓

18. SHELL DETECTS 401 & AUTO-REFRESHES
    POST /auth/refresh
    Headers: Cookie: refresh_token=...
    (httpOnly cookie auto-sent by browser)
    ↓

19. IDENTITY SERVICE RESPONDS WITH NEW ACCESS TOKEN
    200 OK
    {
      "access_token": "eyJhbGc...(new JWT)",
      "expires_in": 3600
    }
    ↓

20. SHELL UPDATES LOCALSTORAGE
    localStorage.setItem('access_token', new_jwt)
    ↓

21. RETRY ORIGINAL REQUEST
    GET /vyapar/api/opportunities
    Headers: Authorization: Bearer eyJhbGc...(new token)
    ✓ Request succeeds
    ↓

22. USER NEVER SEES LOGIN SCREEN AGAIN
    (Token refreshed silently in background)
```

### Key Implementation Details

**Frontend (Shell + Modules):**

```typescript
// src/context/AuthContext.tsx (shell)
import React, { useCallback } from 'react';

interface AuthContextType {
  user: { user_id: string; phone: string } | null;
  tiers: Record<string, string>;  // { vyapar: 'pro', mangaly: 'elite' }
  modules: string[];  // ['vyapar', 'mangaly', 'milavn']
  accessToken: string | null;
  login: (phone: string) => Promise<void>;
  verifyOtp: (phone: string, otp: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthContextType['user']>(null);
  const [tiers, setTiers] = React.useState<Record<string, string>>({});
  const [modules, setModules] = React.useState<string[]>([]);
  const [accessToken, setAccessToken] = React.useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  );

  // Decode JWT and extract claims
  const decodeToken = useCallback((token: string) => {
    const parts = token.split('.');
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  }, []);

  const login = useCallback(async (phone: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/send-otp`, {
      method: 'POST',
      body: JSON.stringify({ phone }),
    });
    if (!response.ok) throw new Error('Failed to send OTP');
  }, []);

  const verifyOtp = useCallback(
    async (phone: string, otp: string) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify-otp`, {
        method: 'POST',
        body: JSON.stringify({ phone, otp }),
      });
      if (!response.ok) throw new Error('Invalid OTP');

      const data = await response.json();
      const token = data.access_token;
      
      // Store tokens
      localStorage.setItem('access_token', token);
      // refresh_token automatically in httpOnly cookie (no JS access)

      // Decode and extract claims
      const decoded = decodeToken(token);
      setAccessToken(token);
      setUser({ user_id: decoded.sub, phone: decoded.phone });
      setTiers(decoded.tiers);
      setModules(decoded.modules);
    },
    [decodeToken]
  );

  const refreshToken = useCallback(async () => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',  // Send httpOnly cookie
    });
    if (!response.ok) {
      // Token refresh failed, redirect to login
      logout();
      return;
    }

    const data = await response.json();
    const newToken = data.access_token;
    localStorage.setItem('access_token', newToken);
    setAccessToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setUser(null);
    setAccessToken(null);
    setTiers({});
    setModules([]);
  }, []);

  return (
    <AuthContext.Provider value={{ user, tiers, modules, accessToken, login, verifyOtp, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

**Backend (API Gateway / Module API):**

```python
# api/middleware/jwt_validation.py (FastAPI)
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
from typing import Dict

security = HTTPBearer()

async def validate_jwt(credentials = Depends(security)) -> Dict:
    """Validate JWT signature, expiry, and extract claims"""
    token = credentials.credentials
    
    try:
        # Use public key from Identity & Trust Service
        # (cached in memory, refreshed periodically)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="forkhatri-platform"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid_token")

# api/endpoints/vyapar.py (example module endpoint)
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/profile")
async def get_profile(jwt_claims: Dict = Depends(validate_jwt)):
    """Get user's professional profile"""
    user_id = jwt_claims['sub']
    tier = jwt_claims['tiers'].get('vyapar')
    
    # Query database to verify tier (in case it changed mid-session)
    profile = await db.query(
        "SELECT * FROM vyapar_professional_profile WHERE user_id = %s",
        [user_id]
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Verify tier from database
    db_tier = profile['tier']
    if db_tier != tier:
        # Database has more recent tier info, use it
        tier = db_tier
    
    # Check authorization: Can this tier see sensitive fields?
    if tier == 'free':
        return {
            "name": profile['name'],
            "category": profile['category'],
            # Hide sensitive fields for free tier
        }
    else:  # pro or elite
        return {
            "name": profile['name'],
            "category": profile['category'],
            "phone": profile['phone'],
            "email": profile['email'],
            "verified_credentials": profile['verified_credentials'],
            # Show all fields for paid tiers
        }

@router.post("/opportunities")
async def create_opportunity(
    jwt_claims: Dict = Depends(validate_jwt),
    opportunity_data: Dict = None
):
    """Create a new opportunity"""
    user_id = jwt_claims['sub']
    tier = jwt_claims['tiers'].get('vyapar')
    
    # Check tier authorization
    if tier == 'free':
        raise HTTPException(status_code=403, detail="Upgrade to pro to post opportunities")
    
    # Verify user hasn't hit rate limit (per MODULE-ARCHITECTURE-STANDARD.md §4c)
    is_rate_limited = await check_rate_limit(user_id, 'create_opportunity', limit=10, window=86400)
    if is_rate_limited:
        raise HTTPException(status_code=429, detail="Rate limited")
    
    # Create opportunity
    opportunity = await db.insert(
        "INSERT INTO vyapar_opportunity (user_id, title, description, tier) VALUES (%s, %s, %s, %s)",
        [user_id, opportunity_data['title'], opportunity_data['description'], tier]
    )
    
    return {"opportunity_id": opportunity['id']}
```

**Auto-Refresh Interceptor (Frontend):**

```typescript
// src/lib/apiClient.ts
import { useAuth } from '@/context/AuthContext';

export function createApiClient(authContext: ReturnType<typeof useAuth>) {
  return {
    async fetch<T>(url: string, options: RequestInit = {}): Promise<T> {
      const headers = {
        'Authorization': `Bearer ${authContext.accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      };

      let response = await fetch(url, { ...options, headers });

      // If 401, try to refresh token
      if (response.status === 401) {
        await authContext.refreshToken();
        
        // Retry with new token
        headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
        response = await fetch(url, { ...options, headers });
      }

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return response.json();
    },
  };
}
```

---

## Summary: How It All Works Together

### Day 1: User Signs Up for ForKhatri

```
1. User opens forkhathri.app
2. Shell shows: "Login" or "Sign up"
3. User enters phone → Identity sends OTP
4. User verifies OTP → Identity creates platform_user record
5. Identity issues JWT with empty tiers/modules: { modules: [] }
6. Shell shows dashboard: "No modules available yet. Check back soon!"
```

### Day 2: User Joins Vyapar (as a Professional)

```
1. User navigates to vyapar.forkhatri.app (from marketing link)
2. Vyapar API checks: Does vyapar_professional_profile exist for this user?
3. If not: Vyapar shows onboarding (create profile, enter business name)
4. User completes onboarding → Vyapar inserts into vyapar_professional_profile
5. Vyapar marks user's tier as 'basic' (free)
6. Next time user logs in:
   - Identity checks all module tables
   - Finds vyapar_professional_profile
   - Encodes in JWT: { tiers: { vyapar: 'basic' }, modules: ['vyapar'] }
   - Shell renders dashboard with "Vyapar" tile
7. User can now enter Vyapar
```

### Day 3: User Upgrades to Vyapar Pro

```
1. In Vyapar, user clicks "Upgrade to Pro"
2. Vyapar calls Payment Services: POST /pay/upgrade
3. Payment Services processes payment
4. Vyapar updates: UPDATE vyapar_professional_profile SET tier = 'pro'
5. On next API call (or token refresh), Identity re-encodes JWT:
   - { tiers: { vyapar: 'pro' }, ... }
6. Vyapar reads JWT claim, shows "pro" features (without re-login)
```

### Day 4: User Joins Mangaly (as a matrimonial member)

```
1. User navigates to mangaly.forkhatri.app (separate link)
2. Mangaly checks: Does mangaly_matrimonial_member exist?
3. If not: Mangaly shows onboarding
4. User creates matrimonial profile → Mangaly inserts record
5. Mangaly sets tier to 'free'
6. On next shell login/token refresh:
   - Identity finds: vyapar_professional_profile + mangaly_matrimonial_member
   - Encodes JWT: { 
       tiers: { vyapar: 'pro', mangaly: 'free' },
       modules: ['vyapar', 'mangaly'],
       roles: { vyapar: ['professional'], mangaly: ['member'] }
     }
7. Shell renders dashboard: "Vyapar" tile (pro) + "Mangaly" tile (free)
8. User can access BOTH modules
   - Vyapar knows: "This person is a pro professional"
   - Mangaly knows: "This person is a free matrimonial member"
   - They are INDEPENDENT tier systems
```

### Day 5: User Switches Modules Without Re-Login

```
1. In Vyapar, user clicks profile menu → "Go to Mangaly"
2. Shell unmounts Vyapar, loads Mangaly via Module Federation
3. Same JWT is passed (not expired)
4. Mangaly renders immediately with user's data
5. No login screen, no OTP, no session re-creation
6. User sees Mangaly with their free tier features
```

---

## Checklist: What Needs to Be Built

### Phase 1: Platform Infrastructure (Foundation) — Blocking
- [ ] **Identity & Trust Service**
  - [ ] Create IdentityDB schema (platform_user, credential, verified_credential, member_reputation)
  - [ ] Implement POST /auth/send-otp (SMS provider integration)
  - [ ] Implement POST /auth/verify-otp (OTP validation, JWT issuance)
  - [ ] Implement POST /auth/refresh (token refresh with refresh_token rotation)
  - [ ] Implement GET /me (return authenticated user info)
  - [ ] Implement JWT signing (RS256, key rotation)
  - [ ] Set public key endpoint for downstream services (GET /auth/public-key)
  - [ ] Deploy to production, set uptime SLA to 99.9%

- [ ] **Module Registry & Access Control** (in Core Platform DB `platform` schema)
  - [ ] Create `modules` table (module_key, name, description, tier_options)
  - [ ] Create `user_module_access` table (user_id, module_key, tier, cached_access)
  - [ ] Implement GET /platform/modules (list available modules)
  - [ ] Implement GET /platform/modules/:module_key/access (check user's access for specific module)
  - [ ] Implement background job: sync user_module_access from each module's user table (run hourly)

### Phase 2: Module Frontend Wrapping (UI/UX) — Can start in parallel with Phase 1
- [ ] **ForKhatri Shell (forkhatri-shell)**
  - [ ] Create Next.js project with Module Federation host configuration
  - [ ] Implement AuthContext (JWT management, token refresh, login/logout)
  - [ ] Implement Login page (phone entry, OTP verification)
  - [ ] Implement Dashboard (module tile listing)
  - [ ] Implement dynamic module loader (Module Federation remotes)
  - [ ] Set up shared scope (React, TailwindCSS, auth context, design tokens)
  - [ ] Deploy to forkhathri.app:3000 (dev), forkhatri.app (prod)

- [ ] **Vyapar Module Federation Setup**
  - [ ] Add Module Federation remote configuration to Next.js
  - [ ] Expose ModuleApp component
  - [ ] Import auth context from shell
  - [ ] Update all API calls to include JWT in Authorization header
  - [ ] Deploy to vyapar.forkhatri.app:3001 (dev), vyapar.forkhatri.app (prod)

- [ ] **Mangaly Module Federation Setup** (BREAKING: removes custom auth)
  - [ ] Add Module Federation remote configuration
  - [ ] **DELETE** custom login/signup endpoints
  - [ ] **DELETE** custom OTP verification
  - [ ] **DELETE** custom member/credential tables
  - [ ] **DELETE** session token generation
  - [ ] Add JWT validation middleware
  - [ ] Add AuthContext integration
  - [ ] Update all API calls to use JWT
  - [ ] Deploy to mangaly.forkhatri.app:3002

- [ ] **Milavn Module Federation Setup**
  - [ ] (Same as Vyapar, since not yet built with custom auth)

### Phase 3: Tier-Based Access Control (Authorization) — Parallel
- [ ] **Per-Module Tier Implementation**
  - [ ] Vyapar: Define tier enum (basic, pro, elite) + features per tier + Stripe/payment integration
  - [ ] Mangaly: Define tier enum (free, premium, elite) + features per tier + Stripe integration
  - [ ] Milavn: Define tier enum (creator, pro) + features per tier
  - [ ] For each module: Add tier validation to sensitive endpoints (upgrade checks, rate limiting, feature gates)

- [ ] **API Gateway or Unified API**
  - [ ] Option A: Kong API Gateway
    - [ ] Set up Kong with module routes
    - [ ] Create Kong plugin for JWT validation
    - [ ] Create Kong plugin for rate limiting (shared across modules)
  - [ ] Option B: Unified FastAPI service
    - [ ] Create main API service that imports each module's router
    - [ ] Implement global JWT validation middleware
    - [ ] Implement module-access enforcement middleware
    - [ ] Route requests to appropriate module handler

### Phase 4: Data Migration (Breaking Change) — Schedule when Mangaly can go offline
- [ ] **Mangaly User Migration**
  - [ ] Export existing mangaly_member records (phone, email, created_at, etc.)
  - [ ] Create Identity platform_user records for each
  - [ ] Map old member_ids to new user_ids in migration table
  - [ ] Update all Mangaly foreign keys (matches, circles, etc.) to new user_ids
  - [ ] Notify users: "Your account has been migrated to ForKhatri. Log in at forkhatri.app"
  - [ ] Provide 7-day support window for login issues

### Phase 5: Testing & Launch
- [ ] Integration testing (shell + modules)
- [ ] E2E tests (login → module switching → tier-based access)
- [ ] Load testing (concurrent logins, module switching)
- [ ] Security audit (JWT validation, token refresh, tier enforcement)
- [ ] Staging deployment
- [ ] Production rollout (with Mangaly user migration)

---

## FAQ: Trust/Reputation Clarification

**Q: "You said each trust factor is different" — what exactly?**

A: Reputation/trust is **context-aware per module**. From PRODUCT-GUARDRAILS.md:
- "A person trusted professionally is not automatically trusted matrimonially"

This means:
- User A might have 95/100 trust score in **Vyapar** (professional context) because:
  - They've closed 50 deals
  - Clients gave 5-star reviews
  - Business is verified with GST
- But the same User A might have 20/100 trust score in **Mangaly** (matrimonial context) because:
  - They're a new profile
  - No attendees yet
  - No community history

**Why it matters for ForKhatri:**
- Vyapar shows "Highly Trusted Professional" badge
- Mangaly shows "New Member" badge
- They're independent signals, not inherited
- Each module's features are based on its own reputation, not "global trust"

**Implementation:**
- `member_reputation` table has `module_context` column
- Reputation score is computed per context (Vyapar feedback ≠ Mangaly feedback)
- Shell/modules never show cross-module trust signals

---

**Status: Ready for implementation. No code changes yet. All architectural decisions made.**

Next: Please confirm you're ready to start, and specify which phase to begin with (Phase 1, Phase 2, etc., or in parallel?).
