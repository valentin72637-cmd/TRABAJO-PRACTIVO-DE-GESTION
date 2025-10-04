<?php
// Incluir en dashboards si quisieras centralizar la verificación (opcional, no usado directamente)
session_start();
if (!isset($_SESSION['user_id'])) {
    header('Location: ../login/index.html?error=session');
    exit;
}
?>
