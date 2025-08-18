# CSRF Token Implementation Guide - Garasade Repository

## Table of Contents
1. [Overview](#overview)
2. [Configuration Architecture](#configuration-architecture)
3. [Template Integration Patterns](#template-integration-patterns)
4. [Backend Validation Logic](#backend-validation-logic)
5. [AJAX/API Handling](#ajaxapi-handling)
6. [Session Management](#session-management)
7. [Error Handling Strategies](#error-handling-strategies)
8. [Webhook Security](#webhook-security)
9. [Testing Considerations](#testing-considerations)
10. [Best Practices and Lessons Learned](#best-practices-and-lessons-learned)

## Overview

The garasade repository implements a comprehensive CSRF (Cross-Site Request Forgery) protection system using Flask-WTF. The implementation follows a layered approach that provides security while maintaining flexibility for different use cases including webhooks, API endpoints, and traditional form submissions.

### Core Components
- **Flask-WTF CSRFProtect**: Central CSRF protection extension
- **Meta tag token distribution**: Tokens embedded in HTML for JavaScript access
- **Global fetch interceptor**: Automatic CSRF header injection for all AJAX requests
- **Selective exemption**: Webhook endpoints exempt from CSRF protection

## Configuration Architecture

### Base Configuration (`config.py`)

```python
# Base configuration class
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration (critical for CSRF)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit on CSRF tokens
```

### Environment-Specific Configurations

```python
class DevelopmentConfig(Config):
    # Development: CSRF disabled for easier testing
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    # Testing: CSRF disabled to simplify test writing
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    # Production: Full CSRF protection enabled
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # WTF_CSRF_ENABLED = True (inherited from base)
```

### Application Initialization (`app/__init__.py`)

```python
from flask_wtf.csrf import CSRFProtect

# Initialize CSRF protection globally
csrf = CSRFProtect()

def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize CSRF protection with app
    csrf.init_app(app)
    
    return app
```

## Template Integration Patterns

### Meta Tag Distribution Strategy

The implementation uses a meta tag in base templates to distribute CSRF tokens to JavaScript code:

#### Base Template (`app/templates/base.html`)
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{% block title %}OUTFOROJ{% endblock %}</title>
</head>
```

### Form Integration

For traditional HTML forms, CSRF tokens are included as hidden inputs:

#### Login Form Example (`app/templates/auth/password_login.html`)
```html
<form method="POST" action="{{ url_for('auth.password_login') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Login</button>
</form>
```

#### Signup Form Example (`app/templates/auth/signup.html`)
```html
<form method="POST" class="space-y-4">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- Form fields -->
</form>
```

### Global Fetch Interceptor (DRY Principle)

The implementation follows the DRY principle by implementing a global fetch interceptor in the base template:

```javascript
<!-- In app/templates/base.html -->
<script>
    // Global CSRF fetch interceptor - automatically adds CSRF token to all same-origin requests
    if (window.fetch) {
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            // Check if same-origin request
            const urlObject = (url instanceof URL) ? url : new URL(url, window.location.origin);
            const isSameOrigin = urlObject.origin === window.location.origin;
            
            if (isSameOrigin) {
                const headers = new Headers(options ? options.headers : {});
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

                if (csrfToken) {
                    headers.set('X-CSRFToken', csrfToken);
                }

                const newOptions = {
                    ...options,
                    headers: headers
                };

                return originalFetch(url, newOptions);
            }
            
            return originalFetch(url, options);
        };
    }
</script>
```

## Backend Validation Logic

### Automatic CSRF Validation

Flask-WTF automatically validates CSRF tokens for:
1. All POST/PUT/PATCH/DELETE requests
2. Both form data (`csrf_token` field) and headers (`X-CSRFToken`)
3. Token presence and validity against session

### Protected Endpoints

Regular API endpoints that require CSRF protection:

```python
@bp.route('/instant-call', methods=['POST'])
@login_required
def instant_call():
    """Protected endpoint - CSRF token required"""
    # CSRF validation happens automatically
    # If token is missing or invalid, Flask-WTF returns 400
    data = request.get_json()
    # Process the request...
```

### CSRF-Exempt Endpoints

Webhooks and external API endpoints that need to bypass CSRF:

```python
from app import csrf

@bp.route('/webhook', methods=['POST'])
@csrf.exempt  # Decorator to exempt from CSRF protection
def stripe_webhook():
    """Webhook endpoint - CSRF protection disabled"""
    # Verify webhook signature instead of CSRF token
    sig_header = request.headers.get('Stripe-Signature')
    # Process webhook...
```

## AJAX/API Handling

### Manual AJAX Request Example

For specific AJAX calls that don't use the global interceptor:

```javascript
// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Make API call with CSRF token
fetch('/api/send-contact-sms', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()  // Include CSRF token
    },
    body: JSON.stringify({ message: 'test' })
})
```

### Real Implementation Examples

#### Contact SMS Sending (`app/templates/main/apple-shortcut.html`)
```javascript
fetch('/api/send-contact-sms', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
    },
    body: JSON.stringify({})
})
```

## Session Management

### Session Configuration Impact on CSRF

```python
# Critical session settings for CSRF
PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Token lifetime
SESSION_COOKIE_HTTPONLY = True                  # Prevent JS access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'                # CSRF mitigation
SESSION_COOKIE_SECURE = True                    # HTTPS only (production)
```

### Session Persistence for CSRF

The implementation ensures session persistence for CSRF token validity:

```python
# In auth_service.py
def login_user_with_session(user):
    login_user(user, remember=True)
    session.permanent = True  # Ensure session persists
    session.modified = True   # Mark session as modified
```

## Error Handling Strategies

### Missing CSRF Token Detection

When a CSRF token is missing, the logs show:
```
flask_wtf.csrf - INFO - The CSRF token is missing.
Response: 400 POST /api/instant-call
```

### Default Error Response

Flask-WTF returns a 400 Bad Request with an HTML error page by default. The implementation includes a generic 400 error handler:

```python
@app.errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html'), 400
```

### Client-Side Error Handling

```javascript
fetch('/api/instant-call', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(data)
})
.then(response => {
    if (response.status === 400) {
        // Handle CSRF error
        console.error('CSRF validation failed');
    }
})
```

## Webhook Security

### CSRF Exemption Pattern

External webhooks (Stripe, Twilio, Vapi) are exempted from CSRF protection:

```python
# Stripe webhook
@bp.route('/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    # Verify using Stripe signature instead
    sig_header = request.headers.get('Stripe-Signature')
    # ...

# Twilio SMS webhook  
@bp.route('/webhook', methods=['POST'])
@csrf.exempt
def sms_webhook():
    # Twilio webhook verification
    # ...

# Vapi AI webhook
@bp.route('/vapi-webhook', methods=['POST'])
@csrf.exempt
def vapi_webhook():
    # Process webhook without CSRF
    # ...
```

### Alternative Security for Webhooks

Instead of CSRF tokens, webhooks use:
1. **Signature Verification**: Stripe webhook signatures
2. **IP Whitelisting**: Could restrict to known service IPs
3. **Request Validation**: Verify expected payload structure
4. **Idempotency**: Handle duplicate webhook deliveries

## Testing Considerations

### Test Configuration

Tests disable CSRF for simplicity:

```python
# tests/conftest.py
class TestConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for tests
```

### Testing with CSRF Enabled

If testing with CSRF enabled:

```python
def test_api_with_csrf(client):
    # Get CSRF token first
    response = client.get('/login')
    csrf_token = extract_csrf_token(response.data)
    
    # Include in request
    response = client.post('/api/instant-call',
        headers={'X-CSRFToken': csrf_token},
        json={'data': 'test'}
    )
```

## Best Practices and Lessons Learned

### 1. Template Inheritance for Security

**Pattern**: Implement security features in base templates
```
base.html (Security Layer)
├── CSRF meta tag
├── Global fetch interceptor
└── Security headers

dashboard.html (extends base.html)
├── Inherits all security features
└── Focuses on business logic
```

### 2. The CSRF Implementation Cycle

From the TIL documentation, the repository experienced repeated CSRF issues:

**Problem History**:
- Multiple commits fixing CSRF in forms but not JavaScript
- Pattern of partial fixes addressing only one aspect

**Resolution**:
1. HTML forms need `{{ csrf_token() }}` hidden inputs
2. JavaScript API calls need `X-CSRFToken` headers
3. Both must be implemented for complete protection

### 3. DRY Principle Application

**Initial Problem**: CSRF code duplicated across templates

**Solution**: Global fetch interceptor in base template
- Single source of truth
- Automatic protection for new pages
- Consistent behavior across application

### 4. Environment-Specific Configuration

```python
# Development/Testing: Easier debugging
WTF_CSRF_ENABLED = False

# Production: Full security
WTF_CSRF_ENABLED = True
SESSION_COOKIE_SECURE = True
```

### 5. Public API Considerations

For public API endpoints that still need user authentication:

```python
@bp.route('/shortcut-call', methods=['POST'])
def shortcut_call():
    # No @login_required decorator
    # Custom authentication via shortcut codes
    # Still protected by CSRF if not exempted
```

### 6. Error Recovery Patterns

```javascript
// Retry logic for CSRF failures
async function apiCallWithRetry(url, options) {
    try {
        return await fetch(url, options);
    } catch (error) {
        if (error.status === 400) {
            // Refresh CSRF token and retry
            const newToken = await refreshCSRFToken();
            options.headers['X-CSRFToken'] = newToken;
            return await fetch(url, options);
        }
        throw error;
    }
}
```

## Security Considerations

### Attack Prevention

The implementation prevents:
1. **Cross-site request forgery**: Malicious sites can't make unauthorized requests
2. **Session hijacking**: Combined with secure session cookies
3. **Replay attacks**: Tokens tied to user sessions

### Defense in Depth

Multiple layers of security:
1. CSRF tokens (primary defense)
2. SameSite cookies (additional CSRF protection)
3. HTTPS-only cookies in production
4. Session expiration

## Migration Guide for Other Repositories

To implement similar CSRF protection:

### Step 1: Install Flask-WTF
```bash
pip install Flask-WTF
```

### Step 2: Configure CSRF
```python
# config.py
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
SECRET_KEY = 'your-secret-key'
```

### Step 3: Initialize CSRF
```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
csrf.init_app(app)
```

### Step 4: Add Meta Tag to Base Template
```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```

### Step 5: Implement Global Interceptor
Copy the fetch interceptor code to your base template

### Step 6: Add Tokens to Forms
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

### Step 7: Exempt Webhooks
```python
@csrf.exempt
def webhook_handler():
    pass
```

## Troubleshooting Common Issues

### Issue 1: "The CSRF token is missing"
**Solution**: Check that:
- Meta tag is present in HTML
- JavaScript includes X-CSRFToken header
- Form includes csrf_token hidden input

### Issue 2: "The CSRF token is invalid"
**Solution**: Verify:
- Session cookies are being sent
- SECRET_KEY hasn't changed
- Session hasn't expired

### Issue 3: Webhooks failing with 400
**Solution**: Add `@csrf.exempt` decorator

### Issue 4: Tests failing with CSRF errors
**Solution**: Set `WTF_CSRF_ENABLED = False` in test config

## Conclusion

The garasade CSRF implementation demonstrates a mature, production-ready approach to web application security. Key strengths include:

1. **Comprehensive coverage**: Both forms and AJAX protected
2. **DRY principle**: Global interceptor prevents duplication
3. **Flexible exemptions**: Webhooks can bypass when needed
4. **Environment awareness**: Different settings for dev/test/prod
5. **Well-documented issues**: TIL files capture lessons learned

This implementation serves as an excellent reference for adding CSRF protection to Flask applications while maintaining developer productivity and code maintainability.