<?php
session_start();
require_once __DIR__ . '/db.php';

function redirect_with_error($code) {
    header('Location: ../login/index.html?error=' . urlencode($code));
    exit;
}

if (empty($_POST['email']) || empty($_POST['password'])) {
    redirect_with_error('required');
}

$email = trim($_POST['email']);
$password = $_POST['password'];

// Consulta segura
$stmt = $mysqli->prepare('SELECT id, nombre, email, password_hash, rol FROM users WHERE email = ? LIMIT 1');
$stmt->bind_param('s', $email);
$stmt->execute();
$result = $stmt->get_result();

if ($row = $result->fetch_assoc()) {
    if (password_verify($password, $row['password_hash'])) {
        // Sesión segura
        session_regenerate_id(true);
        $_SESSION['user_id'] = $row['id'];
        $_SESSION['user_name'] = $row['nombre'];
        $_SESSION['user_email'] = $row['email'];
        $_SESSION['user_role'] = $row['rol'];

        // Redirección por rol
        if ($row['rol'] === 'admin') {
            header('Location: ./dashboard_admin.php');
        } else {
            header('Location: ./dashboard_cliente.php');
        }
        exit;
    }
}

// Falla
redirect_with_error('invalid');
?>
