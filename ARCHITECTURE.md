# GiHaNotis Architecture

## What Is GiHaNotis?

GiHaNotis is a web application for managing resource needs during crises (like natural disasters). Think of it as a digital bulletin board where:

- **Coordinators** post what supplies they need (e.g., "We need 50 blankets")
- **Volunteers** can see these needs and offer to help (e.g., "I have 10 blankets available")

---

## How It Works (Simple Overview)

```
┌─────────────────────────────────────────────────────────────┐
│                        USERS                                │
│                                                             │
│   👤 Public Users              👤 Administrators            │
│   (Volunteers)                 (Crisis Coordinators)        │
│   - View open requests         - Create/edit requests       │
│   - Submit offers to help      - Accept/manage responses    │
│                                - Close fulfilled requests   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     WEB APPLICATION                         │
│                     (Flask Server)                          │
│                                                             │
│   Handles all user interactions, validates data,            │
│   enforces security rules, and manages sessions             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATABASE                              │
│                     (PostgreSQL)                            │
│                                                             │
│   Stores all requests and responses permanently             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Three Main Parts

### 1. User Interface (What People See)

| Interface | Who Uses It | What They Can Do |
|-----------|-------------|------------------|
| **Public Pages** | Anyone | View needed items, offer to help |
| **Admin Dashboard** | Coordinators (with login) | Create requests, manage responses |
| **API Documentation** | Developers | Understand how to integrate |

### 2. Web Server (The "Brain")

The server processes all requests and makes sure:
- Only authorized users can access admin features
- All submitted data is safe and valid
- Requests and responses are properly stored
- Pages load quickly

### 3. Database (The "Memory")

Stores two types of information:

| Table | What It Stores | Example |
|-------|---------------|---------|
| **Requests** | Items needed | "Need 20 shovels for debris removal" |
| **Responses** | Offers from volunteers | "I have 5 shovels, located at Main St" |

---

## Data Flow Example

**Scenario: A volunteer offers to help with a request**

```
1. Volunteer visits the public page
         │
         ▼
2. Sees "Need 50 blankets" request
         │
         ▼
3. Clicks "I Can Help" and fills form:
   - Quantity: 10 blankets
   - Location: 123 Oak Street
   - Contact: volunteer@email.com
         │
         ▼
4. Server validates the data
   (checks for errors, removes harmful content)
         │
         ▼
5. Response saved to database
         │
         ▼
6. Coordinator sees new response in admin panel
         │
         ▼
7. Coordinator clicks "Accept"
   → Quantity needed drops from 50 to 40
```

---

## Security Layers

| Protection | What It Does |
|------------|--------------|
| **Login Required** | Only coordinators can create/manage requests |
| **Rate Limiting** | Prevents spam (max 5 login attempts per minute) |
| **Session Timeout** | Auto-logout after 8 hours of inactivity |
| **Input Sanitization** | Removes harmful code from user submissions |
| **CSRF Protection** | Prevents fake form submissions |

---

## Key URLs

| URL | Purpose |
|-----|---------|
| `/` | Public view - see all open requests |
| `/admin` | Coordinator login and dashboard |
| `/health` | System status check |
| `/docs` | API documentation |

---

## Technology Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | Flask (Python) | Handles web requests |
| Database | PostgreSQL | Stores data |
| Frontend | Bootstrap 5 | Makes pages look nice |
| Deployment | Docker | Easy setup anywhere |

---

## File Organization

```
GiHaNotis/
├── app.py           ← Main application logic
├── config.py        ← Settings and configuration
├── db.py            ← Database connection handling
├── validation.py    ← Data validation rules
├── templates/       ← HTML page templates
├── static/          ← CSS styles and API spec
└── docker files     ← Container deployment
```

---

## Summary

GiHaNotis is a simple request-response system:

1. **Coordinators** post what they need
2. **Volunteers** offer what they have
3. **Coordinators** accept offers and track fulfillment
4. **Everyone** can see what's still needed

The application prioritizes simplicity and security, making it easy to deploy and use during crisis situations when quick coordination is essential.
