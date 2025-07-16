<?php

// --- CONFIGURATION ---
// Centralize settings for easy changes.
$pythonCommand = 'python3'; // or 'python', or '/usr/bin/python3'
$scriptPath = 'py/main.py';
$valid_purposes = [
    "objective", "outcomes", "pedagogy", "development", 
    "implementation", "evaluation", "integrator"
];


// --- SCRIPT START ---

// Set the correct JSON header AT THE BEGINNING.
// This is the most important fix.
header('Content-Type: application/json');

/**
 * Helper function to send a standardized JSON error response and exit.
 * @param string $message The error message.
 *  @param int $http_code The HTTP status code to send.
 */
function send_json_error($message, $http_code = 500) {
    http_response_code($http_code);
    echo json_encode([
        'type' => 'error',
        'summary' => $message
    ]);
    exit;
}

// --- 1. Get and Validate Input ---
$json_data = file_get_contents('php://input');
$data = json_decode($json_data);

if (!$data || !isset($data->userInput) || !isset($data->purpose)) {
    send_json_error("Invalid input. 'userInput' and 'purpose' are required.", 400);
}

$userInput = $data->userInput;
$purpose = $data->purpose;

// NEW: Validate that the purpose is one we expect.
if (!in_array($purpose, $valid_purposes)) {
    send_json_error("Invalid 'purpose' provided: " . htmlspecialchars($purpose), 400);
}


// --- 2. Execute Python Script using proc_open ---

// escapeshellarg makes the 'purpose' safe to pass as a command-line argument
$safePurpose = escapeshellarg($purpose);
$command = $pythonCommand . " " . $scriptPath . " " . $safePurpose;

$descriptorspec = [
   0 => ["pipe", "r"],  // stdin
   1 => ["pipe", "w"],  // stdout
   2 => ["pipe", "w"]   // stderr
];

$process = proc_open($command, $descriptorspec, $pipes);

if (is_resource($process)) {
    // Write the large userInput string to the Python script's stdin
    fwrite($pipes[0], $userInput);
    fclose($pipes[0]);

    // Read the Python script's output from stdout
    $output = stream_get_contents($pipes[1]);
    fclose($pipes[1]);

    // Read any errors from stderr
    $errors = stream_get_contents($pipes[2]);
    fclose($pipes[2]);

    proc_close($process);

    if (!empty($errors)) {
        // If the Python script printed to stderr, format it as a standard JSON error.
        send_json_error("Python Script Error: " . trim($errors));
    } else {
        // The Python script already outputs perfect JSON.
        // We just need to echo it directly. The header is already set.
        echo trim($output);
    }
} else {
    send_json_error("Failed to execute the Python script.");
}

?>