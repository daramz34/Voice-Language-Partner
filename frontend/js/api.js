/* API helper — token storage + calls to the backend. */

const API = {
  base: "",  // same origin — uvicorn serves frontend and api together
  token: localStorage.getItem("token"),

  saveToken(token) {
    this.token = token;
    localStorage.setItem("token", token);
  },

  clearToken() {
    this.token = null;
    localStorage.removeItem("token");
  },

  // If the backend says 401, our JWT is expired/invalid —
  // clear it and send the user to login with a friendly message.
  handleExpired(res) {
    if (res.status === 401) {
      this.clearToken();
      window.location.href = "/auth.html?expired=1";
      return true;
    }
    return false;
  },

  headers() {
    return { Authorization: `Bearer ${this.token}` };
  },

  async register({ username, email, password, native_language }) {
    const res = await fetch(`${this.base}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password, native_language }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail?.[0]?.msg || data.detail || "Registration failed");
    return data;
  },

  async login(username, password) {
    // OAuth2PasswordRequestForm expects form-encoded fields, not JSON
    const res = await fetch(`${this.base}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Login failed");
    this.saveToken(data.access_token);
    return data;
  },

  async me() {
    const res = await fetch(`${this.base}/api/v1/auth/me`, {
      headers: this.headers(),
    });
    if (this.handleExpired(res)) return null;
    if (!res.ok) return null;
    return res.json();
  },

  async createSession(payload) {
    const res = await fetch(`${this.base}/api/v1/session/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...this.headers() },
      body: JSON.stringify(payload),
    });
    if (this.handleExpired(res)) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail?.[0]?.msg || data.detail || "Could not create session");
    return data;
  },

  async endSession(id, payload) {
    const res = await fetch(`${this.base}/api/v1/session/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...this.headers() },
      body: JSON.stringify(payload),
    });
    if (this.handleExpired(res)) return null;
    if (!res.ok) throw new Error("Could not end session");
    return res.json();
  },

  async getTranscript(id) {
    const res = await fetch(`${this.base}/api/v1/session/${id}/transcript`, { headers: this.headers() });
    if (this.handleExpired(res)) return [];
    if (!res.ok) return [];
    return res.json();
  },

  async evaluate(id) {
    const res = await fetch(`${this.base}/api/v1/session/${id}/evaluate`, {
      method: "POST", headers: this.headers(),
    });
    if (this.handleExpired(res)) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Evaluation failed");
    return data;
  },

  async voiceToken() {
    const res = await fetch(`${this.base}/api/v1/voice/token`);
    if (!res.ok) throw new Error("Could not get voice token");
    return res.json();
  },
    async saveMessage(sessionId, speaker, content, language) {
    // fire-and-forget persistence — don't await strictly
    const res = await fetch(`${this.base}/api/v1/session/${sessionId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...this.headers() },
      body: JSON.stringify({ session_id: Number(sessionId), speaker, content, language }),
    });
    if (this.handleExpired(res)) return null;
    return res.ok ? res.json() : null;
  },

};
