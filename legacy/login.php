<?php
session_start();
require_once __DIR__ . '/db.php';

function redirect_with_error($code) {
    header('Location: ../login/index.html?error=' . urlencode($code));
    exit;
}

// Validar campos
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

        // Guardar también en localStorage (modo Go Live sin backend persistente)
        echo "<script>
            localStorage.setItem('usuario_actual', JSON.stringify({
                nombre: '{$row['nombre']}',
                email: '{$row['email']}',
                rol: '{$row['rol']}'
            }));
            window.location.href = '" . ($row['rol'] === 'admin'
                ? "../login/app/dashboard_admin.html"
                : "../login/app/dashboard_cliente.html") . "';
        </script>";
        exit;
    }
}

// Si el login falla
redirect_with_error('invalid');
?>
