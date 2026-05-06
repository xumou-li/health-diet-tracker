export function isSuperAdmin(user) {
  return Number(user?.role) === 2
}

export function canEditSystemConfig(user) {
  return isSuperAdmin(user)
}
