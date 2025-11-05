<?php
// backend/header/header.php
// Header común del backend: inicia sesión de forma segura (solo si no está iniciada)
// y renderiza la barra superior. NO debe incluir <html> ni <body> completo,
// se espera que se incluya dentro del <body> de las páginas.

if (session_status() === PHP_SESSION_NONE) {
    // Opcional: definir parámetros de cookie de sesión seguros antes de iniciar
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'domain' => '', // dejar vacío o ajustar si tenés dominio
        'secure' => isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}
?>
<link rel="stylesheet" href="/backend/header/header.css">

<header class="main-header">
  <nav class="navbar">
    <div class="logo">
      <a href="/index.html">Mi Proyecto</a>
    </div>

    <ul class="nav-links">
      <li><a href="/backend/dashboard_admin.php">Inicio</a></li>
      <li><a href="/backend/dashboard_cliente.php">Clientes</a></li>
      <?php if (!empty($_SESSION['user_id'])): ?>
        <li><a href="/backend/logout.php">Cerrar sesión</a></li>
      <?php else: ?>
        <li><a href="/login/index.html">Ingresar</a></li>
      <?php endif; ?>
    </ul>

    <div class="user-info">
      <?php if (!empty($_SESSION['user_name'])): ?>
        <span class="small">Hola, <?php echo htmlspecialchars($_SESSION['user_name']); ?></span>
      <?php endif; ?>
    </div>
  </nav>
</header>
