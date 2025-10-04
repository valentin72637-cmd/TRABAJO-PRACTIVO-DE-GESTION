<?php
session_start();
if (!isset($_SESSION['user_id'])) {
    header('Location: ../login/index.html?error=session');
    exit;
}
if ($_SESSION['user_role'] !== 'admin') {
    header('Location: ../login/index.html?error=role');
    exit;
}
?>
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Panel Admin</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<nav class="navbar navbar-expand-lg bg-body-tertiary">
  <div class="container">
    <a class="navbar-brand" href="#">Seguros</a>
    <div class="d-flex">
      <span class="navbar-text me-3">Hola, <?php echo htmlspecialchars($_SESSION['user_name']); ?></span>
      <a class="btn btn-outline-danger btn-sm" href="./logout.php">Salir</a>
    </div>
  </div>
</nav>
<main class="container py-4">
  <div class="alert alert-primary">Accediste como <strong>admin</strong>.</div>
  <div class="card">
    <div class="card-body">
      <h1 class="h4">Panel de Administración</h1>
      <p class="text-muted">Aquí irían funciones para administrar usuarios, pólizas, etc.</p>
    </div>
  </div>
</main>
</body>
</html>
