export function requireAuth(roles = []) {
  const data = localStorage.getItem('auth');
  if (!data) {
    window.location.href = '../index.html?error=session';
    return;
  }

  const user = JSON.parse(data);
  if (roles.length && !roles.includes(user.rol)) {
    window.location.href = '../index.html?error=role';
    return;
  }

  document.getElementById('username')?.textContent = user.nombre;
  document.getElementById('userrole')?.textContent = user.rol;
  return user;
}
