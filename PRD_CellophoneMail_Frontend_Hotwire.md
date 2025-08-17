# CellophoneMail Frontend Application PRD
## TailwindCSS + Hotwire (Stimulus + Turbo) with Python Litestar Backend

**Version:** 1.0  
**Date:** August 17, 2025  
**Tech Stack:** TailwindCSS + Hotwire (Stimulus + Turbo) + Python Litestar  

---

## 1. Executive Summary

CellophoneMail is an AI-powered email protection SaaS that uses the "Four Horsemen" framework to detect and filter toxic communication. This PRD defines the frontend application architecture using modern server-rendered HTML with progressive enhancement via Hotwire technologies.

### Key Features
- Server-rendered HTML with SPA-like navigation
- Real-time dashboard updates using Turbo Streams
- Progressive enhancement with Stimulus controllers
- Responsive design with TailwindCSS utility classes
- Session-based authentication with Litestar backend

---

## 2. Technical Architecture

### 2.1 Core Technology Stack

**Frontend Framework:** Hotwire (Stimulus + Turbo)
- **Turbo Drive:** SPA-like navigation without JavaScript frameworks
- **Turbo Frames:** Lazy-loaded page sections and modals
- **Turbo Streams:** Real-time updates via WebSocket/SSE
- **Stimulus:** Lightweight JavaScript controllers for interactivity

**Styling:** TailwindCSS
- Utility-first CSS framework
- Responsive design patterns
- Component composition via CSS classes
- No custom CSS beyond Tailwind utilities

**Backend:** Python Litestar
- Server-rendered Jinja2 templates
- RESTful API endpoints
- Session-based authentication
- WebSocket support for real-time features

### 2.2 Application Architecture

```
┌─────────────────────────────────────────┐
│              Browser                     │
│  ┌─────────────┐  ┌─────────────────────┐│
│  │  Stimulus   │  │     Turbo           ││
│  │ Controllers │  │ Drive/Frames/Streams││
│  └─────────────┘  └─────────────────────┘│
└─────────────────────────────────────────┘
                    │ HTTP/WebSocket
┌─────────────────────────────────────────┐
│           Litestar Backend              │
│  ┌─────────────┐  ┌─────────────────────┐│
│  │  Templates  │  │    Controllers      ││
│  │   (Jinja2)  │  │   (HTML + API)      ││
│  └─────────────┘  └─────────────────────┘│
│  ┌─────────────┐  ┌─────────────────────┐│
│  │ Auth System │  │   Four Horsemen     ││
│  │ (Sessions)  │  │    AI Analysis      ││
│  └─────────────┘  └─────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 3. Page Specifications

### 3.1 Landing Page (`/`)

**Purpose:** Marketing page to introduce CellophoneMail and drive user registration

**Template:** `templates/landing.html`

**Layout Structure:**
```html
<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
  <nav class="px-6 py-4 flex justify-between items-center">
    <div class="text-2xl font-bold text-indigo-600">CellophoneMail</div>
    <div class="space-x-4">
      <a href="/auth/login" class="text-gray-600 hover:text-indigo-600">Log In</a>
      <a href="/auth/register" class="bg-indigo-600 text-white px-4 py-2 rounded-lg">Sign Up</a>
    </div>
  </nav>
  
  <div class="max-w-6xl mx-auto px-6 py-16 text-center">
    <h1 class="text-5xl font-bold text-gray-900 mb-6">
      Stop Toxic Emails Before They Hurt
    </h1>
    <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
      AI-powered email protection using the Four Horsemen framework to detect criticism, 
      contempt, defensiveness, and stonewalling before they reach your inbox.
    </p>
    <div class="space-x-4">
      <a href="/auth/register" 
         class="bg-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-700">
        Start Free Trial
      </a>
    </div>
  </div>
</section>

<!-- Four Horsemen Explanation -->
<section class="py-16 bg-white">
  <div class="max-w-6xl mx-auto px-6">
    <h2 class="text-3xl font-bold text-center mb-12">The Four Horsemen of Toxic Communication</h2>
    <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
      <!-- Criticism Card -->
      <div class="bg-red-50 p-6 rounded-lg border border-red-200">
        <div class="text-red-600 text-2xl mb-4">🗣️</div>
        <h3 class="font-bold text-red-800 mb-2">Criticism</h3>
        <p class="text-red-700 text-sm">Attacks on character rather than specific behavior</p>
      </div>
      
      <!-- Contempt Card -->
      <div class="bg-orange-50 p-6 rounded-lg border border-orange-200">
        <div class="text-orange-600 text-2xl mb-4">😤</div>
        <h3 class="font-bold text-orange-800 mb-2">Contempt</h3>
        <p class="text-orange-700 text-sm">Expressions of superiority and disrespect</p>
      </div>
      
      <!-- Defensiveness Card -->
      <div class="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
        <div class="text-yellow-600 text-2xl mb-4">🛡️</div>
        <h3 class="font-bold text-yellow-800 mb-2">Defensiveness</h3>
        <p class="text-yellow-700 text-sm">Playing victim and making excuses</p>
      </div>
      
      <!-- Stonewalling Card -->
      <div class="bg-gray-50 p-6 rounded-lg border border-gray-200">
        <div class="text-gray-600 text-2xl mb-4">🧱</div>
        <h3 class="font-bold text-gray-800 mb-2">Stonewalling</h3>
        <p class="text-gray-700 text-sm">Emotional withdrawal and shutting down</p>
      </div>
    </div>
  </div>
</section>
```

**Stimulus Controller:** `landing_controller.js`
```javascript
// app/javascript/controllers/landing_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["heroSection", "ctaButton"]
  
  connect() {
    // Animate hero section on load
    this.animateHero()
  }
  
  animateHero() {
    // Simple fade-in animation
    this.heroSectionTarget.style.opacity = "0"
    this.heroSectionTarget.style.transform = "translateY(20px)"
    
    setTimeout(() => {
      this.heroSectionTarget.style.transition = "all 0.6s ease"
      this.heroSectionTarget.style.opacity = "1"
      this.heroSectionTarget.style.transform = "translateY(0)"
    }, 100)
  }
  
  trackCTAClick(event) {
    // Analytics tracking for signup conversions
    console.log("CTA clicked:", event.target.textContent)
  }
}
```

---

### 3.2 Sign Up Page (`/auth/register`)

**Purpose:** User registration with two signup flows (Individual and Organization)

**Template:** `templates/auth/register.html`

**Litestar Controller:** `auth.py` (extend existing)
```python
# New methods to add to existing AuthController

@get("/register")
async def get_register_form(self) -> Template:
    """Display registration form."""
    return Template("auth/register.html", context={
        "page_title": "Create Account - CellophoneMail",
        "signup_flows": ["individual", "organization"]
    })

@post("/register")
async def process_registration(self, data: UserRegistration) -> Response:
    """Process registration form submission."""
    # Existing registration logic with enhanced error handling
    try:
        user = await create_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name
        )
        
        # Return Turbo-compatible response for success
        return Template("auth/register_success.html", context={
            "user": user,
            "shield_address": f"{user.username}@cellophanemail.com"
        })
        
    except ValidationError as e:
        # Return Turbo-compatible error response
        return Template("auth/register.html", context={
            "errors": e.errors(),
            "form_data": data.dict()
        }, status_code=422)
```

**Template Structure:**
```html
<!-- templates/auth/register.html -->
<turbo-frame id="registration-form">
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Create your account
      </h2>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        
        <!-- Signup Flow Selector -->
        <div data-controller="signup-flow" class="mb-6">
          <div class="grid grid-cols-2 gap-3">
            <button data-action="click->signup-flow#selectFlow" 
                    data-flow="individual"
                    class="signup-flow-btn bg-indigo-50 border border-indigo-200 text-indigo-700 px-4 py-2 rounded-lg">
              Individual
            </button>
            <button data-action="click->signup-flow#selectFlow" 
                    data-flow="organization"
                    class="signup-flow-btn bg-gray-50 border border-gray-200 text-gray-700 px-4 py-2 rounded-lg">
              Organization
            </button>
          </div>
        </div>

        <!-- Registration Form -->
        <form data-controller="registration-form" 
              data-action="submit->registration-form#submit"
              data-turbo-frame="registration-form"
              action="/auth/register" 
              method="POST" 
              class="space-y-6">
          
          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <div class="mt-1">
              <input data-registration-form-target="email"
                     id="email" 
                     name="email" 
                     type="email" 
                     autocomplete="email" 
                     required
                     class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div class="mt-1 relative">
              <input data-registration-form-target="password"
                     id="password" 
                     name="password" 
                     type="password" 
                     autocomplete="new-password" 
                     required
                     class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
              <div data-registration-form-target="passwordStrength" 
                   class="mt-1 text-xs text-gray-500"></div>
            </div>
          </div>

          <!-- Dynamic Fields Container -->
          <div data-signup-flow-target="dynamicFields" data-flow="individual">
            <!-- Individual Fields -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="first_name" class="block text-sm font-medium text-gray-700">
                  First name
                </label>
                <input type="text" name="first_name" id="first_name"
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
              </div>
              <div>
                <label for="last_name" class="block text-sm font-medium text-gray-700">
                  Last name
                </label>
                <input type="text" name="last_name" id="last_name"
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
              </div>
            </div>
          </div>

          <!-- Error Display -->
          <div data-registration-form-target="errors" class="hidden">
            <div class="rounded-md bg-red-50 p-4">
              <div class="text-sm text-red-700" data-registration-form-target="errorMessage"></div>
            </div>
          </div>

          <!-- Submit Button -->
          <div>
            <button type="submit" 
                    data-registration-form-target="submitButton"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
              <span data-registration-form-target="submitText">Create Account</span>
              <div data-registration-form-target="spinner" class="hidden ml-2">
                <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </button>
          </div>
        </form>

        <!-- Login Link -->
        <div class="mt-6 text-center">
          <a href="/auth/login" class="text-indigo-600 hover:text-indigo-500">
            Already have an account? Sign in
          </a>
        </div>
      </div>
    </div>
  </div>
</turbo-frame>
```

**Stimulus Controllers:**

**1. Signup Flow Controller** (`signup_flow_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["dynamicFields"]
  static values = { currentFlow: String }
  
  connect() {
    this.currentFlowValue = "individual"
  }
  
  selectFlow(event) {
    const flow = event.target.dataset.flow
    this.currentFlowValue = flow
    
    // Update button styles
    this.updateFlowButtons(flow)
    
    // Update form fields
    this.updateDynamicFields(flow)
  }
  
  updateFlowButtons(selectedFlow) {
    this.element.querySelectorAll('.signup-flow-btn').forEach(btn => {
      const flow = btn.dataset.flow
      if (flow === selectedFlow) {
        btn.className = "signup-flow-btn bg-indigo-50 border border-indigo-200 text-indigo-700 px-4 py-2 rounded-lg"
      } else {
        btn.className = "signup-flow-btn bg-gray-50 border border-gray-200 text-gray-700 px-4 py-2 rounded-lg"
      }
    })
  }
  
  updateDynamicFields(flow) {
    const fieldsContainer = this.dynamicFieldsTarget
    
    if (flow === "organization") {
      fieldsContainer.innerHTML = `
        <div>
          <label for="company" class="block text-sm font-medium text-gray-700">
            Organization name
          </label>
          <input type="text" name="company" id="company" required
                 class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
        </div>
        <div>
          <label for="team_size" class="block text-sm font-medium text-gray-700">
            Team size
          </label>
          <select name="team_size" id="team_size" required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            <option value="">Select team size</option>
            <option value="1-10">1-10 members</option>
            <option value="11-50">11-50 members</option>
            <option value="51-200">51-200 members</option>
            <option value="200+">200+ members</option>
          </select>
        </div>
      `
    } else {
      fieldsContainer.innerHTML = `
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="first_name" class="block text-sm font-medium text-gray-700">
              First name
            </label>
            <input type="text" name="first_name" id="first_name"
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
          </div>
          <div>
            <label for="last_name" class="block text-sm font-medium text-gray-700">
              Last name
            </label>
            <input type="text" name="last_name" id="last_name"
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
          </div>
        </div>
      `
    }
  }
}
```

**2. Registration Form Controller** (`registration_form_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["email", "password", "passwordStrength", "errors", "errorMessage", "submitButton", "submitText", "spinner"]
  
  connect() {
    this.setupPasswordValidation()
  }
  
  setupPasswordValidation() {
    this.passwordTarget.addEventListener('input', () => {
      this.validatePasswordStrength()
    })
  }
  
  validatePasswordStrength() {
    const password = this.passwordTarget.value
    const strength = this.calculatePasswordStrength(password)
    
    this.passwordStrengthTarget.innerHTML = `
      <div class="flex items-center space-x-2">
        <div class="flex space-x-1">
          ${this.renderStrengthBars(strength.score)}
        </div>
        <span class="${strength.color}">${strength.text}</span>
      </div>
      ${strength.requirements.length > 0 ? `
        <ul class="mt-1 text-xs text-gray-500">
          ${strength.requirements.map(req => `<li>• ${req}</li>`).join('')}
        </ul>
      ` : ''}
    `
  }
  
  calculatePasswordStrength(password) {
    const requirements = []
    let score = 0
    
    if (password.length < 8) requirements.push("At least 8 characters")
    else score++
    
    if (!/[A-Z]/.test(password)) requirements.push("One uppercase letter")
    else score++
    
    if (!/[a-z]/.test(password)) requirements.push("One lowercase letter")  
    else score++
    
    if (!/\d/.test(password)) requirements.push("One number")
    else score++
    
    const strengthLevels = [
      { text: "Very Weak", color: "text-red-600" },
      { text: "Weak", color: "text-orange-600" },
      { text: "Fair", color: "text-yellow-600" },
      { text: "Good", color: "text-blue-600" },
      { text: "Strong", color: "text-green-600" }
    ]
    
    return {
      score,
      requirements,
      ...strengthLevels[score]
    }
  }
  
  renderStrengthBars(score) {
    return Array(4).fill().map((_, i) => {
      const active = i < score
      const color = active ? this.getBarColor(score) : "bg-gray-200"
      return `<div class="h-1 w-6 rounded ${color}"></div>`
    }).join('')
  }
  
  getBarColor(score) {
    const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"]
    return colors[score - 1] || "bg-gray-200"
  }
  
  submit(event) {
    event.preventDefault()
    
    this.showLoading()
    this.hideErrors()
    
    // Let Turbo handle the form submission
    const form = event.target
    fetch(form.action, {
      method: form.method,
      body: new FormData(form),
      headers: {
        'Accept': 'text/vnd.turbo-stream.html'
      }
    })
    .then(response => response.text())
    .then(html => {
      if (html.includes('turbo-stream')) {
        // Handle Turbo Stream response
        Turbo.renderStreamMessage(html)
      } else {
        // Handle regular HTML response
        this.element.innerHTML = html
      }
    })
    .catch(error => {
      this.showError("Registration failed. Please try again.")
    })
    .finally(() => {
      this.hideLoading()
    })
  }
  
  showLoading() {
    this.submitButtonTarget.disabled = true
    this.submitTextTarget.textContent = "Creating Account..."
    this.spinnerTarget.classList.remove('hidden')
  }
  
  hideLoading() {
    this.submitButtonTarget.disabled = false
    this.submitTextTarget.textContent = "Create Account"
    this.spinnerTarget.classList.add('hidden')
  }
  
  showError(message) {
    this.errorMessageTarget.textContent = message
    this.errorsTarget.classList.remove('hidden')
  }
  
  hideErrors() {
    this.errorsTarget.classList.add('hidden')
  }
}
```

---

### 3.3 Log In Page (`/auth/login`)

**Purpose:** User authentication with password reset functionality

**Template:** `templates/auth/login.html`

**Litestar Controller Enhancement:**
```python
@get("/login")
async def get_login_form(self) -> Template:
    """Display login form."""
    return Template("auth/login.html", context={
        "page_title": "Sign In - CellophoneMail"
    })

@post("/login")
async def process_login(self, data: UserLogin, request: Request) -> Response:
    """Process login form submission."""
    try:
        user = await authenticate_user(data.email, data.password)
        
        if not user:
            return Template("auth/login.html", context={
                "error": "Invalid email or password",
                "email": data.email
            }, status_code=401)
        
        # Create session
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        
        # Redirect to dashboard
        return Redirect("/dashboard")
        
    except Exception as e:
        return Template("auth/login.html", context={
            "error": "Login failed. Please try again.",
            "email": data.email
        }, status_code=500)

@get("/forgot-password")
async def get_forgot_password_form(self) -> Template:
    """Display forgot password form."""
    return Template("auth/forgot_password.html")

@post("/forgot-password") 
async def process_forgot_password(self, email: EmailStr) -> Template:
    """Process forgot password request."""
    # Send password reset email
    await send_password_reset_email(email)
    
    return Template("auth/forgot_password_sent.html", context={
        "email": email
    })
```

**Template Structure:**
```html
<!-- templates/auth/login.html -->
<turbo-frame id="login-form">
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-indigo-600 mb-2">CellophoneMail</h1>
        <h2 class="text-2xl font-bold text-gray-900">Sign in to your account</h2>
      </div>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        
        <form data-controller="login-form"
              data-action="submit->login-form#submit"
              data-turbo-frame="login-form"
              action="/auth/login" 
              method="POST" 
              class="space-y-6">
          
          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <div class="mt-1">
              <input data-login-form-target="email"
                     id="email" 
                     name="email" 
                     type="email" 
                     autocomplete="email" 
                     required
                     value="{{ email or '' }}"
                     class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div class="mt-1">
              <input data-login-form-target="password"
                     id="password" 
                     name="password" 
                     type="password" 
                     autocomplete="current-password" 
                     required
                     class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
          </div>

          <!-- Remember Me & Forgot Password -->
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input id="remember-me" name="remember-me" type="checkbox" 
                     class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
              <label for="remember-me" class="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>

            <div class="text-sm">
              <a href="/auth/forgot-password" 
                 data-turbo-frame="login-form"
                 class="font-medium text-indigo-600 hover:text-indigo-500">
                Forgot your password?
              </a>
            </div>
          </div>

          <!-- Error Display -->
          {% if error %}
          <div class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
          </div>
          {% endif %}

          <!-- Submit Button -->
          <div>
            <button type="submit" 
                    data-login-form-target="submitButton"
                    class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
              <span data-login-form-target="submitText">Sign in</span>
              <div data-login-form-target="spinner" class="hidden ml-2">
                <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </button>
          </div>
        </form>

        <!-- Sign Up Link -->
        <div class="mt-6 text-center">
          <a href="/auth/register" class="text-indigo-600 hover:text-indigo-500">
            Don't have an account? Sign up
          </a>
        </div>
      </div>
    </div>
  </div>
</turbo-frame>
```

**Login Form Controller** (`login_form_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["email", "password", "submitButton", "submitText", "spinner"]
  
  submit(event) {
    event.preventDefault()
    
    this.showLoading()
    
    // Let Turbo handle the form submission  
    const form = event.target
    form.submit()
  }
  
  showLoading() {
    this.submitButtonTarget.disabled = true
    this.submitTextTarget.textContent = "Signing in..."
    this.spinnerTarget.classList.remove('hidden')
  }
  
  hideLoading() {
    this.submitButtonTarget.disabled = false
    this.submitTextTarget.textContent = "Sign in" 
    this.spinnerTarget.classList.add('hidden')
  }
}
```

---

### 3.4 Main Dashboard (`/dashboard`)

**Purpose:** Display email filtering analytics with real-time updates

**Template:** `templates/dashboard/index.html`

**Litestar Controller:**
```python
# New dashboard controller: src/cellophanemail/routes/dashboard.py

from litestar import get, Controller
from litestar.response import Template
from litestar.security.session_auth import SessionAuth
from typing import Dict, Any
from cellophanemail.services.dashboard_service import (
    get_user_stats,
    get_recent_activity,
    get_horsemen_breakdown
)

class DashboardController(Controller):
    """Dashboard and analytics."""
    
    path = "/dashboard"
    guards = [session_auth_guard]  # Require authentication
    
    @get("/")
    async def dashboard_home(self, request: Request) -> Template:
        """Main dashboard page."""
        user_id = request.session["user_id"]
        
        # Get dashboard data
        stats = await get_user_stats(user_id)
        recent_activity = await get_recent_activity(user_id, limit=10)
        horsemen_breakdown = await get_horsemen_breakdown(user_id)
        
        return Template("dashboard/index.html", context={
            "page_title": "Dashboard - CellophoneMail",
            "user_email": request.session["email"],
            "stats": stats,
            "recent_activity": recent_activity,
            "horsemen_breakdown": horsemen_breakdown
        })
    
    @get("/stats-stream")
    async def stats_stream(self, request: Request) -> TurboStream:
        """Real-time stats updates via Turbo Stream."""
        user_id = request.session["user_id"]
        
        # Get latest stats
        stats = await get_user_stats(user_id)
        
        # Return Turbo Stream update
        return TurboStream(
            action="replace",
            target="dashboard-stats",
            template="dashboard/partials/stats.html",
            context={"stats": stats}
        )

router = DashboardController
```

**Template Structure:**
```html
<!-- templates/dashboard/index.html -->
{% extends "layouts/dashboard_base.html" %}

{% block content %}
<div data-controller="dashboard" 
     data-dashboard-user-id-value="{{ request.session.user_id }}"
     class="space-y-6">
  
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-gray-600">Welcome back, {{ user_email }}</p>
    </div>
    <div class="flex items-center space-x-4">
      <div class="text-sm text-gray-500">
        Shield Address: <span class="font-mono text-indigo-600">{{ user.username }}@cellophanemail.com</span>
      </div>
    </div>
  </div>

  <!-- Stats Cards -->
  <turbo-frame id="dashboard-stats" data-controller="stats-updater">
    {% include "dashboard/partials/stats.html" %}
  </turbo-frame>

  <!-- Four Horsemen Breakdown -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Four Horsemen Analysis</h2>
      <p class="text-sm text-gray-600">Breakdown of filtered emails by toxicity type</p>
    </div>
    
    <div class="p-6">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Criticism -->
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-3 bg-red-100 rounded-full flex items-center justify-center">
            <span class="text-2xl">🗣️</span>
          </div>
          <div class="text-2xl font-bold text-red-600">{{ horsemen_breakdown.criticism }}</div>
          <div class="text-sm text-gray-600">Criticism</div>
        </div>
        
        <!-- Contempt -->
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-3 bg-orange-100 rounded-full flex items-center justify-center">
            <span class="text-2xl">😤</span>
          </div>
          <div class="text-2xl font-bold text-orange-600">{{ horsemen_breakdown.contempt }}</div>
          <div class="text-sm text-gray-600">Contempt</div>
        </div>
        
        <!-- Defensiveness -->
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-3 bg-yellow-100 rounded-full flex items-center justify-center">
            <span class="text-2xl">🛡️</span>
          </div>
          <div class="text-2xl font-bold text-yellow-600">{{ horsemen_breakdown.defensiveness }}</div>
          <div class="text-sm text-gray-600">Defensiveness</div>
        </div>
        
        <!-- Stonewalling -->
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-3 bg-gray-100 rounded-full flex items-center justify-center">
            <span class="text-2xl">🧱</span>
          </div>
          <div class="text-2xl font-bold text-gray-600">{{ horsemen_breakdown.stonewalling }}</div>
          <div class="text-sm text-gray-600">Stonewalling</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Recent Activity Feed -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Recent Activity</h2>
    </div>
    
    <turbo-frame id="activity-feed" data-controller="activity-stream">
      {% include "dashboard/partials/activity_feed.html" %}
    </turbo-frame>
  </div>
</div>
{% endblock %}
```

**Stats Partial Template:**
```html
<!-- templates/dashboard/partials/stats.html -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <!-- Total Emails Processed -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
          </svg>
        </div>
      </div>
      <div class="ml-4">
        <p class="text-sm font-medium text-gray-600">Total Emails</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.total_emails }}</p>
      </div>
    </div>
    <div class="mt-4">
      <span class="text-sm text-green-600">+{{ stats.emails_this_week }} this week</span>
    </div>
  </div>

  <!-- Filtered/Blocked -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636"></path>
          </svg>
        </div>
      </div>
      <div class="ml-4">
        <p class="text-sm font-medium text-gray-600">Filtered</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.filtered_emails }}</p>
      </div>
    </div>
    <div class="mt-4">
      <span class="text-sm text-gray-600">{{ stats.filter_rate }}% filter rate</span>
    </div>
  </div>

  <!-- Safe Emails -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
      </div>
      <div class="ml-4">
        <p class="text-sm font-medium text-gray-600">Safe</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.safe_emails }}</p>
      </div>
    </div>
    <div class="mt-4">
      <span class="text-sm text-green-600">{{ stats.safety_rate }}% safe rate</span>
    </div>
  </div>
</div>
```

**Activity Feed Partial:**
```html
<!-- templates/dashboard/partials/activity_feed.html -->
<div class="divide-y divide-gray-200">
  {% for activity in recent_activity %}
  <div class="p-6 flex items-start space-x-4">
    <div class="flex-shrink-0">
      {% if activity.classification == 'SAFE' %}
        <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
      {% elif activity.classification == 'WARNING' %}
        <div class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
        </div>
      {% elif activity.classification == 'HARMFUL' %}
        <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
      {% else %}
        <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
          <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636"></path>
          </svg>
        </div>
      {% endif %}
    </div>
    
    <div class="flex-1 min-w-0">
      <div class="flex items-center justify-between">
        <p class="text-sm font-medium text-gray-900">
          Email from {{ activity.sender_email }}
        </p>
        <time class="text-xs text-gray-500">{{ activity.created_at | timeago }}</time>
      </div>
      
      <div class="mt-1 flex items-center space-x-2">
        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium 
                     {% if activity.classification == 'SAFE' %}bg-green-100 text-green-800
                     {% elif activity.classification == 'WARNING' %}bg-yellow-100 text-yellow-800
                     {% elif activity.classification == 'HARMFUL' %}bg-orange-100 text-orange-800
                     {% else %}bg-red-100 text-red-800{% endif %}">
          {{ activity.classification }}
        </span>
        
        {% if activity.horsemen_detected %}
          {% for horseman in activity.horsemen_detected %}
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
              {{ horseman | title }}
            </span>
          {% endfor %}
        {% endif %}
      </div>
      
      {% if activity.subject %}
      <p class="mt-1 text-sm text-gray-600 truncate">
        Subject: {{ activity.subject }}
      </p>
      {% endif %}
    </div>
  </div>
  {% endfor %}
</div>
```

**Dashboard Controller** (`dashboard_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { userId: String }
  
  connect() {
    this.startRealtimeUpdates()
  }
  
  disconnect() {
    this.stopRealtimeUpdates()
  }
  
  startRealtimeUpdates() {
    // Connect to WebSocket for real-time updates
    this.websocket = new WebSocket(`ws://localhost:8000/ws/dashboard/${this.userIdValue}`)
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleRealtimeUpdate(data)
    }
    
    // Fallback polling every 30 seconds
    this.pollInterval = setInterval(() => {
      this.refreshStats()
    }, 30000)
  }
  
  stopRealtimeUpdates() {
    if (this.websocket) {
      this.websocket.close()
    }
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  }
  
  handleRealtimeUpdate(data) {
    if (data.type === 'new_email') {
      // Update stats and activity feed
      this.refreshStats()
      this.refreshActivityFeed()
    }
  }
  
  refreshStats() {
    fetch(`/dashboard/stats-stream`, {
      headers: {
        'Accept': 'text/vnd.turbo-stream.html'
      }
    })
    .then(response => response.text())
    .then(html => {
      Turbo.renderStreamMessage(html)
    })
  }
  
  refreshActivityFeed() {
    const frame = document.querySelector('#activity-feed')
    if (frame) {
      frame.reload()
    }
  }
}
```

---

### 3.5 Watch List Page (`/watchlist`)

**Purpose:** Manage blocked/abusive email addresses

**Template:** `templates/watchlist/index.html`

**Litestar Controller:**
```python
# New watchlist controller: src/cellophanemail/routes/watchlist.py

from litestar import get, post, delete, Controller
from litestar.response import Template, Redirect
from litestar.security.session_auth import SessionAuth
from pydantic import BaseModel, EmailStr
from cellophanemail.services.watchlist_service import (
    get_user_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    search_watchlist
)

class WatchlistEntry(BaseModel):
    email: EmailStr
    reason: str = "Toxic communication"
    auto_block: bool = True

class WatchlistController(Controller):
    """Watchlist management."""
    
    path = "/watchlist"
    guards = [session_auth_guard]  # Require authentication
    
    @get("/")
    async def watchlist_home(self, request: Request, search: str = "") -> Template:
        """Watchlist management page."""
        user_id = request.session["user_id"]
        
        if search:
            entries = await search_watchlist(user_id, search)
        else:
            entries = await get_user_watchlist(user_id)
        
        return Template("watchlist/index.html", context={
            "page_title": "Watch List - CellophoneMail",
            "entries": entries,
            "search_query": search
        })
    
    @post("/add")
    async def add_watchlist_entry(self, request: Request, data: WatchlistEntry) -> Response:
        """Add email to watchlist."""
        user_id = request.session["user_id"]
        
        try:
            await add_to_watchlist(
                user_id=user_id,
                email=data.email,
                reason=data.reason,
                auto_block=data.auto_block
            )
            
            return TurboStream(
                action="append",
                target="watchlist-entries",
                template="watchlist/partials/entry.html",
                context={"entry": data}
            )
            
        except Exception as e:
            return TurboStream(
                action="replace",
                target="add-entry-errors",
                content=f'<div class="text-red-600 text-sm">{str(e)}</div>'
            )
    
    @delete("/{entry_id:int}")
    async def remove_watchlist_entry(self, request: Request, entry_id: int) -> Response:
        """Remove email from watchlist."""
        user_id = request.session["user_id"]
        
        await remove_from_watchlist(user_id, entry_id)
        
        return TurboStream(
            action="remove",
            target=f"watchlist-entry-{entry_id}"
        )

router = WatchlistController
```

**Template Structure:**
```html
<!-- templates/watchlist/index.html -->
{% extends "layouts/dashboard_base.html" %}

{% block content %}
<div data-controller="watchlist" class="space-y-6">
  
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Watch List</h1>
      <p class="text-gray-600">Manage blocked and abusive email addresses</p>
    </div>
    
    <button data-action="click->watchlist#showAddModal"
            class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
      Add Email
    </button>
  </div>

  <!-- Search and Filters -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <form data-controller="search" 
          data-action="submit->search#submit input->search#search"
          class="space-y-4">
      
      <div class="flex space-x-4">
        <div class="flex-1">
          <input data-search-target="input"
                 type="text" 
                 name="search"
                 value="{{ search_query }}"
                 placeholder="Search by email address or reason..."
                 class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
        </div>
        <button type="submit" 
                class="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200">
          Search
        </button>
      </div>
    </form>
  </div>

  <!-- Watchlist Entries -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Blocked Addresses</h2>
    </div>
    
    <div id="watchlist-entries" class="divide-y divide-gray-200">
      {% for entry in entries %}
        {% include "watchlist/partials/entry.html" %}
      {% endfor %}
      
      {% if not entries %}
      <div class="p-8 text-center">
        <div class="text-gray-400 text-6xl mb-4">📋</div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No blocked addresses</h3>
        <p class="text-gray-600">Add email addresses to automatically block toxic senders.</p>
      </div>
      {% endif %}
    </div>
  </div>

  <!-- Add Entry Modal -->
  <turbo-frame id="add-entry-modal" data-watchlist-target="modal" class="hidden">
    <!-- Modal content will be loaded here -->
  </turbo-frame>
</div>
{% endblock %}
```

**Entry Partial Template:**
```html
<!-- templates/watchlist/partials/entry.html -->
<div id="watchlist-entry-{{ entry.id }}" 
     class="p-6 flex items-center justify-between hover:bg-gray-50">
  
  <div class="flex items-center space-x-4">
    <div class="flex-shrink-0">
      <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
        <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636"></path>
        </svg>
      </div>
    </div>
    
    <div>
      <p class="text-sm font-medium text-gray-900">{{ entry.email }}</p>
      <p class="text-sm text-gray-600">{{ entry.reason }}</p>
      <div class="flex items-center mt-1 space-x-4">
        <span class="text-xs text-gray-500">Added {{ entry.created_at | timeago }}</span>
        {% if entry.auto_block %}
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
            Auto-block enabled
          </span>
        {% endif %}
      </div>
    </div>
  </div>
  
  <div class="flex items-center space-x-2">
    <button data-action="click->watchlist#editEntry"
            data-entry-id="{{ entry.id }}"
            class="text-gray-400 hover:text-gray-600">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
      </svg>
    </button>
    
    <button data-action="click->watchlist#removeEntry"
            data-entry-id="{{ entry.id }}"
            data-confirm="Remove {{ entry.email }} from watch list?"
            class="text-red-400 hover:text-red-600">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
      </svg>
    </button>
  </div>
</div>
```

**Watchlist Controller** (`watchlist_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["modal"]
  
  showAddModal() {
    // Load add modal via Turbo Frame
    const modal = this.modalTarget
    modal.src = "/watchlist/add-form"
    modal.classList.remove('hidden')
  }
  
  hideModal() {
    this.modalTarget.classList.add('hidden')
  }
  
  removeEntry(event) {
    const entryId = event.target.dataset.entryId
    const confirmMessage = event.target.dataset.confirm
    
    if (confirm(confirmMessage)) {
      fetch(`/watchlist/${entryId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'text/vnd.turbo-stream.html'
        }
      })
      .then(response => response.text())
      .then(html => {
        Turbo.renderStreamMessage(html)
      })
    }
  }
  
  editEntry(event) {
    const entryId = event.target.dataset.entryId
    // Load edit form in modal
    const modal = this.modalTarget
    modal.src = `/watchlist/${entryId}/edit`
    modal.classList.remove('hidden')
  }
}
```

**Search Controller** (`search_controller.js`)
```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input"]
  
  search() {
    // Debounced search
    clearTimeout(this.timeout)
    this.timeout = setTimeout(() => {
      this.performSearch()
    }, 300)
  }
  
  submit(event) {
    event.preventDefault()
    this.performSearch()
  }
  
  performSearch() {
    const query = this.inputTarget.value
    const url = new URL(window.location)
    url.searchParams.set('search', query)
    
    // Navigate with Turbo
    Turbo.visit(url.toString())
  }
}
```

---

## 4. Technical Implementation Details

### 4.1 Litestar Template Integration

**Template Configuration:**
```python
# src/cellophanemail/config/templates.py

from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from jinja2 import Environment

def create_template_config() -> TemplateConfig:
    """Create Jinja2 template configuration."""
    
    def timeago_filter(dt):
        """Human-readable time ago filter."""
        # Implementation for "2 hours ago" formatting
        pass
    
    def nl2br_filter(text):
        """Convert newlines to HTML breaks."""
        return text.replace('\n', '<br>')
    
    # Custom filters
    filters = {
        'timeago': timeago_filter,
        'nl2br': nl2br_filter
    }
    
    return TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
        auto_reload=True,  # Development only
        filters=filters
    )
```

**Base Layout Template:**
```html
<!-- templates/layouts/base.html -->
<!DOCTYPE html>
<html lang="en" data-controller="application">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title or "CellophoneMail - AI Email Protection" }}</title>
    
    <!-- TailwindCSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Hotwire -->
    <script type="module">
        import hotwiredTurbo from 'https://cdn.skypack.dev/@hotwired/turbo';
    </script>
    <script type="module" src="/static/js/application.js"></script>
    
    <!-- CSRF Token -->
    <meta name="csrf-token" content="{{ request.session.csrf_token }}">
</head>
<body class="bg-gray-50">
    {% block content %}{% endblock %}
    
    <!-- Toast Notifications -->
    <div id="toast-container" class="fixed top-4 right-4 z-50 space-y-2"></div>
</body>
</html>
```

**Dashboard Layout:**
```html
<!-- templates/layouts/dashboard_base.html -->
{% extends "layouts/base.html" %}

{% block content %}
<div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/dashboard" class="text-xl font-bold text-indigo-600">
                        CellophoneMail
                    </a>
                    <div class="ml-8 space-x-8">
                        <a href="/dashboard" 
                           class="text-gray-900 hover:text-indigo-600 px-3 py-2 text-sm font-medium">
                            Dashboard
                        </a>
                        <a href="/watchlist" 
                           class="text-gray-500 hover:text-indigo-600 px-3 py-2 text-sm font-medium">
                            Watch List
                        </a>
                    </div>
                </div>
                
                <div class="flex items-center space-x-4">
                    <div class="text-sm text-gray-700">{{ request.session.email }}</div>
                    <form action="/auth/logout" method="POST">
                        <button type="submit" 
                                class="text-gray-500 hover:text-gray-700 text-sm">
                            Sign out
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {% block content %}{% endblock %}
    </main>
</div>
{% endblock %}
```

### 4.2 Real-time Updates with Turbo Streams

**WebSocket Integration:**
```python
# src/cellophanemail/routes/websockets.py

from litestar import WebSocket, websocket
from litestar.exceptions import WebSocketException
import json

@websocket("/ws/dashboard/{user_id:str}")
async def dashboard_websocket(socket: WebSocket, user_id: str) -> None:
    """Real-time dashboard updates."""
    await socket.accept()
    
    try:
        # Subscribe to user's email events
        while True:
            # Wait for new email events
            message = await wait_for_email_event(user_id)
            
            # Send Turbo Stream update
            await socket.send_text(json.dumps({
                "type": "turbo_stream",
                "html": render_turbo_stream_update(message)
            }))
            
    except WebSocketException:
        pass
    finally:
        await socket.close()

def render_turbo_stream_update(message) -> str:
    """Render Turbo Stream HTML for real-time updates."""
    return f'''
    <turbo-stream action="prepend" target="activity-feed">
        <template>
            {render_activity_item(message)}
        </template>
    </turbo-stream>
    '''
```

**Client-side WebSocket Handler:**
```javascript
// app/javascript/controllers/realtime_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { endpoint: String }
  
  connect() {
    this.connectWebSocket()
  }
  
  disconnect() {
    if (this.websocket) {
      this.websocket.close()
    }
  }
  
  connectWebSocket() {
    this.websocket = new WebSocket(this.endpointValue)
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'turbo_stream') {
        Turbo.renderStreamMessage(data.html)
      }
    }
    
    this.websocket.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(() => this.connectWebSocket(), 3000)
    }
  }
}
```

### 4.3 Form Handling with Stimulus

**Form Validation Controller:**
```javascript
// app/javascript/controllers/form_validation_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["field", "error"]
  static classes = ["invalid", "valid"]
  
  validate(event) {
    const field = event.target
    const value = field.value
    const rules = this.getValidationRules(field)
    
    const errors = this.validateField(value, rules)
    this.displayErrors(field, errors)
  }
  
  validateField(value, rules) {
    const errors = []
    
    if (rules.required && !value.trim()) {
      errors.push("This field is required")
    }
    
    if (rules.email && value && !this.isValidEmail(value)) {
      errors.push("Please enter a valid email address")
    }
    
    if (rules.minLength && value.length < rules.minLength) {
      errors.push(`Must be at least ${rules.minLength} characters`)
    }
    
    return errors
  }
  
  displayErrors(field, errors) {
    const errorContainer = field.parentNode.querySelector('[data-error-for]')
    
    if (errors.length > 0) {
      field.classList.add(this.invalidClass)
      field.classList.remove(this.validClass)
      
      if (errorContainer) {
        errorContainer.textContent = errors[0]
        errorContainer.classList.remove('hidden')
      }
    } else {
      field.classList.remove(this.invalidClass)
      field.classList.add(this.validClass)
      
      if (errorContainer) {
        errorContainer.classList.add('hidden')
      }
    }
  }
  
  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }
  
  getValidationRules(field) {
    return {
      required: field.hasAttribute('required'),
      email: field.type === 'email',
      minLength: field.getAttribute('minlength')
    }
  }
}
```

### 4.4 Session Authentication

**Session Auth Guard:**
```python
# src/cellophanemail/auth/guards.py

from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler

def session_auth_guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None:
    """Require valid session for protected routes."""
    
    if isinstance(connection, Request):
        if not connection.session.get("user_id"):
            raise NotAuthorizedException("Authentication required")
```

**Session Management:**
```python
# src/cellophanemail/services/session_service.py

from litestar import Request
from typing import Optional
from cellophanemail.models.user import User

async def get_current_user(request: Request) -> Optional[User]:
    """Get current authenticated user from session."""
    user_id = request.session.get("user_id")
    
    if not user_id:
        return None
    
    return await User.objects().where(User.id == user_id).first()

async def create_user_session(request: Request, user: User):
    """Create authenticated session for user."""
    request.session["user_id"] = str(user.id)
    request.session["email"] = user.email
    request.session["csrf_token"] = generate_csrf_token()

async def destroy_user_session(request: Request):
    """Destroy user session."""
    request.session.clear()
```

---

## 5. User Stories with Implementation Notes

### 5.1 User Registration Story

**As a new user, I want to register for CellophoneMail so that I can protect my email from toxic communication.**

**Acceptance Criteria:**
- [x] User can choose between Individual and Organization signup
- [x] Form validates email uniqueness and password strength
- [x] Real-time password strength indicator
- [x] Server-side validation with error handling
- [x] Automatic shield address generation
- [x] Success page with next steps

**Hotwire Implementation:**
- **Turbo Frame** wraps registration form for seamless updates
- **Stimulus Controller** handles signup flow switching and password validation
- **Server-rendered** form with progressive enhancement
- **Turbo Drive** provides SPA-like navigation to dashboard

### 5.2 Dashboard Analytics Story

**As a user, I want to see real-time analytics of filtered emails so that I understand the protection CellophoneMail provides.**

**Acceptance Criteria:**
- [x] Display total emails, filtered emails, and safe emails
- [x] Show Four Horsemen breakdown with visual indicators
- [x] Real-time activity feed of recent email analysis
- [x] Auto-refresh stats every 30 seconds
- [x] WebSocket updates for instant new email notifications

**Hotwire Implementation:**
- **Turbo Streams** for real-time stat updates
- **WebSocket** integration for instant notifications
- **Stimulus Controllers** manage real-time data refreshing
- **Turbo Frames** for lazy-loading activity feed sections

### 5.3 Watch List Management Story

**As a user, I want to manage a watch list of blocked emails so that I can prevent specific senders from reaching me.**

**Acceptance Criteria:**
- [x] View all blocked email addresses
- [x] Add new emails to watch list with reasons
- [x] Search and filter watch list entries
- [x] Remove emails from watch list
- [x] Auto-block toggle for each entry

**Hotwire Implementation:**
- **Turbo Frames** for modal forms (add/edit entries)
- **Stimulus Controllers** handle search, form submission, and entry management
- **Turbo Streams** for adding/removing entries without page reload
- **Server-rendered** search results with URL state management

---

## 6. Performance and UX Considerations

### 6.1 Progressive Enhancement Strategy

**Core Principle:** Application works without JavaScript, enhanced with Stimulus
- Base HTML forms submit normally
- Turbo intercepts and enhances navigation
- Stimulus adds interactive behaviors
- Graceful degradation for unsupported browsers

### 6.2 Loading States and Feedback

**Implementation:**
```javascript
// Loading state management
showLoading() {
  this.submitButton.disabled = true
  this.spinner.classList.remove('hidden')
  this.submitText.textContent = "Processing..."
}

hideLoading() {
  this.submitButton.disabled = false  
  this.spinner.classList.add('hidden')
  this.submitText.textContent = "Submit"
}
```

### 6.3 Real-time Update Strategy

**WebSocket First, Polling Fallback:**
1. Attempt WebSocket connection for real-time updates
2. Fall back to 30-second polling if WebSocket fails
3. Exponential backoff for reconnection attempts
4. Visual indicators for connection status

### 6.4 Mobile Responsiveness

**TailwindCSS Responsive Design:**
- Mobile-first utility classes (`sm:`, `md:`, `lg:`)
- Touch-friendly button sizing (minimum 44px)
- Responsive navigation with hamburger menu
- Optimized form layouts for mobile screens

---

## 7. Security Considerations

### 7.1 CSRF Protection

**Implementation:**
- CSRF tokens in all forms
- Automatic token validation in Litestar
- Token rotation on login/logout
- Exclude webhook endpoints from CSRF

### 7.2 Session Security

**Configuration:**
```python
session_config = SessionConfig(
    secret_key=settings.secret_key,
    cookie_name="cellophane_session",
    cookie_httponly=True,
    cookie_secure=True,  # HTTPS only
    cookie_samesite="strict",
    max_age=86400  # 24 hours
)
```

### 7.3 Content Security Policy

**Headers:**
```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.skypack.dev; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self' ws: wss:;"
)
```

---

## 8. Deployment and Development

### 8.1 Asset Pipeline

**Static Assets Structure:**
```
static/
├── css/
│   └── application.css  # Custom CSS if needed
├── js/
│   ├── application.js   # Stimulus application
│   └── controllers/     # Stimulus controllers
│       ├── dashboard_controller.js
│       ├── registration_form_controller.js
│       └── watchlist_controller.js
└── images/
    └── logo.svg
```

### 8.2 Environment Configuration

**Development:**
```python
# .env.development
DEBUG=true
TURBO_STREAM_SIGNED_STREAM_NAME=development_stream
WEBSOCKET_URL=ws://localhost:8000
```

**Production:**
```python  
# .env.production
DEBUG=false
TURBO_STREAM_SIGNED_STREAM_NAME=production_stream
WEBSOCKET_URL=wss://api.cellophanemail.com
```

### 8.3 Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "cellophanemail.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. Testing Strategy

### 9.1 Integration Tests

**Template Rendering Tests:**
```python
def test_dashboard_renders_correctly(client, authenticated_user):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard - CellophoneMail" in response.text
    assert authenticated_user.email in response.text
```

**Turbo Stream Tests:**
```python  
def test_add_watchlist_entry_returns_turbo_stream(client, authenticated_user):
    response = client.post("/watchlist/add", json={
        "email": "spam@example.com",
        "reason": "Toxic sender"
    }, headers={"Accept": "text/vnd.turbo-stream.html"})
    
    assert response.status_code == 200
    assert "turbo-stream" in response.text
    assert "spam@example.com" in response.text
```

### 9.2 Stimulus Controller Tests

**JavaScript Testing with Jest:**
```javascript
// tests/controllers/registration_form_controller.test.js
import { Application } from "@hotwired/stimulus"
import RegistrationFormController from "../../app/javascript/controllers/registration_form_controller"

describe("RegistrationFormController", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <form data-controller="registration-form">
        <input data-registration-form-target="password" type="password">
        <div data-registration-form-target="passwordStrength"></div>
      </form>
    `
    
    const application = Application.start()
    application.register("registration-form", RegistrationFormController)
  })
  
  test("displays password strength indicator", () => {
    const passwordInput = document.querySelector('[data-registration-form-target="password"]')
    passwordInput.value = "weak"
    passwordInput.dispatchEvent(new Event('input'))
    
    const strengthIndicator = document.querySelector('[data-registration-form-target="passwordStrength"]')
    expect(strengthIndicator.textContent).toContain("Weak")
  })
})
```

---

## 10. Success Metrics

### 10.1 Performance Metrics

**Target Metrics:**
- Page load time: < 2 seconds
- Time to interactive: < 3 seconds  
- First contentful paint: < 1.5 seconds
- Real-time update latency: < 500ms

### 10.2 User Experience Metrics

**Measurement:**
- Form completion rate: > 85%
- Dashboard engagement time: > 2 minutes
- Feature adoption rate: > 60%
- User retention (7-day): > 70%

### 10.3 Technical Metrics

**Monitoring:**
- WebSocket connection success rate: > 95%
- Turbo navigation success rate: > 98%
- JavaScript error rate: < 1%
- Session authentication success: > 99%

---

## Conclusion

This PRD defines a modern, server-rendered SaaS application using Hotwire technologies that provides a fast, responsive user experience without heavy JavaScript frameworks. The architecture leverages Litestar's powerful backend capabilities with Turbo's real-time features and Stimulus's progressive enhancement approach to create an intuitive email protection platform.

The implementation prioritizes:
- **Performance** through server-rendered HTML and minimal JavaScript
- **User Experience** via real-time updates and responsive design  
- **Maintainability** using progressive enhancement and clear separation of concerns
- **Security** through session-based authentication and CSRF protection
- **Scalability** with efficient WebSocket connections and optimized database queries

This architecture provides a solid foundation for building additional features like team management, advanced analytics, and integration capabilities while maintaining the fast, server-rendered approach that makes Hotwire applications performant and accessible.