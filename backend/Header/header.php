<?php include 'backend/header/header.php'; ?>
<link rel="stylesheet" href="backend/header/header.css">

<?php
// Iniciamos la sesión (por si necesitás mostrar el nombre del usuario logueado)
session_start();
?>

<header class="main-header">
  <nav class="navbar">
    <div class="logo">
      <a href="/index.html">Mi Proyecto</a>
    </div>
    <ul class="nav-links">
      <li><a href="/backend/dashboard_admin.php">Inicio</a></li>
      <li><a href="/backend/dashboard_cliente.php">Clientes</a></li>
      <li><a href="/backend/login/logout.php">Cerrar sesión</a></li>
    </ul>
  </nav>
</header>
