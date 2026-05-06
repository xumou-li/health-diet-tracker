export const ADMIN_TOKEN_KEY = 'admin_token'
export const ADMIN_USER_KEY = 'admin_user'

export function getAdminToken() {
  return window.localStorage.getItem(ADMIN_TOKEN_KEY) || ''
}

export function setAdminToken(token) {
  if (!token) {
    window.localStorage.removeItem(ADMIN_TOKEN_KEY)
    return
  }

  window.localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function getAdminUser() {
  const raw = window.localStorage.getItem(ADMIN_USER_KEY)

  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw)
  } catch (error) {
    window.localStorage.removeItem(ADMIN_USER_KEY)
    return null
  }
}

export function setAdminUser(user) {
  if (!user) {
    window.localStorage.removeItem(ADMIN_USER_KEY)
    return
  }

  window.localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(user))
}

export function clearAdminAuth() {
  window.localStorage.removeItem(ADMIN_TOKEN_KEY)
  window.localStorage.removeItem(ADMIN_USER_KEY)
}

export function isAdminAuthenticated() {
  return Boolean(getAdminToken())
}
