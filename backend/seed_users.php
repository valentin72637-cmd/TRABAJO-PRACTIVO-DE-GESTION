<?php
// Ejecutar una sola vez para crear usuarios demo.
require_once __DIR__ . '/db.php';

$users = [
    [
        'nombre' => 'Administrador Demo',
        'email' => 'admin@demo.com',
        'password' => 'Admin123!',
        'rol' => 'admin'
    ],
    [
        'nombre' => 'Cliente Demo',
        'email' => 'cliente@demo.com',
        'password' => 'Cliente123!',
        'rol' => 'cliente'
    ],
];

$created = 0;
foreach ($users as $u) {
    // Verificar si existe por email
    $stmt = $mysqli->prepare('SELECT id FROM users WHERE email = ?');
    $stmt->bind_param('s', $u['email']);
    $stmt->execute();
    $stmt->store_result();
    if ($stmt->num_rows > 0) {
        continue;
    }
    $stmt->close();

    $hash = password_hash($u['password'], PASSWORD_DEFAULT);
    $stmt = $mysqli->prepare('INSERT INTO users(nombre, email, password_hash, rol) VALUES(?, ?, ?, ?)');
    $stmt->bind_param('ssss', $u['nombre'], $u['email'], $hash, $u['rol']);
    if ($stmt->execute()) { $created++; }
    $stmt->close();
}

echo "Usuarios creados: {$created}. Si es 0, ya existían.";
?>
