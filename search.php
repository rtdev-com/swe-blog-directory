<?php
$query = isset($_GET['q']) ? strtolower(trim($_GET['q'])) : '';
if (!$query) {
    echo json_encode(["error" => "No query provided"]);
    exit;
}

// Load JSON file
$jsonData = file_get_contents("search_data.json");
if (!$jsonData) {
    echo json_encode(["error" => "Failed to load JSON file"]);
    exit;
}

$data = json_decode($jsonData, true);
if ($data === null) {
    echo json_encode(["error" => "JSON Decode Error: " . json_last_error_msg()]);
    exit;
}

// Ensure the JSON is an array
if (!is_array($data)) {
    echo json_encode(["error" => "Unexpected JSON structure"]);
    exit;
}

// Search logic
$results = [];
foreach ($data as $item) {
    if (
        (isset($item["title"]) && stripos($item["title"], $query) !== false) ||
        (isset($item["description"]) && stripos($item["description"], $query) !== false) ||
        (isset($item["content"]) && stripos($item["content"], $query) !== false)
    ) {
        $results[] = $item;
    }
    if (count($results) >= 10) break;
}

// Return results as JSON
echo json_encode($results);
?>
