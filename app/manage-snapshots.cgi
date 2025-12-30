#!/usr/bin/env bash

set -euo pipefail

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer - Manage Snapshots</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
EOF

cat header.htm | sed 's/>Snapshot</>Manage Snapshots</'

cat <<'EOF'
<style>
  .snapshot-table {
    border-collapse: collapse;
    margin: 20px 0;
    min-width: 500px;
  }
  .snapshot-table th, .snapshot-table td {
    border: 1px solid #ddd;
    padding: 10px 15px;
    text-align: left;
  }
  .snapshot-table th {
    background: #f5f5f5;
  }
  .snapshot-table tr:hover {
    background: #f9f9f9;
  }
  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    margin: 2px;
  }
  .btn-danger {
    background: #E65A27;
    color: white;
  }
  .btn-danger:hover {
    background: #c44a1f;
  }
  .btn-primary {
    background: #669936;
    color: white;
  }
  .btn-primary:hover {
    background: #557a2d;
  }
  .actions-section {
    margin: 20px 0;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 6px;
  }

  /* Custom Modal Dialog */
  .modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
  }
  .modal-overlay.active {
    display: flex;
  }
  .modal-dialog {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    max-width: 400px;
    width: 90%;
    animation: modalSlideIn 0.2s ease-out;
  }
  @keyframes modalSlideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  .modal-header {
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .modal-header h3 {
    margin: 0;
    font-size: 18px;
  }
  .modal-header.danger h3 {
    color: #E65A27;
  }
  .modal-header.primary h3 {
    color: #669936;
  }
  .modal-close {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
    line-height: 1;
  }
  .modal-close:hover {
    color: #333;
  }
  .modal-body {
    padding: 20px;
    color: #555;
    line-height: 1.5;
  }
  .modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
  .btn-secondary {
    background: #6c757d;
    color: white;
  }
  .btn-secondary:hover {
    background: #5a6268;
  }
</style>

<!-- Custom Modal Dialog -->
<div id="modal-overlay" class="modal-overlay">
  <div class="modal-dialog">
    <div class="modal-header" id="modal-header">
      <h3 id="modal-title">Confirm</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body">
      <p id="modal-message"></p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn" id="modal-confirm-btn" onclick="modalConfirm()">Confirm</button>
    </div>
  </div>
</div>

<div class="actions-section">
  <h3 style="margin-top: 0;">Actions</h3>
  <button class="btn btn-primary" onclick="confirmScan()">Start New Scan</button>
</div>

<h3>Available Snapshots</h3>
<table class="snapshot-table" id="snapshots-table">
  <thead>
    <tr>
      <th>Snapshot</th>
      <th>Used Storage</th>
      <th>Snapshot Size</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody id="snapshots-body">
    <tr><td colspan="4">Loading...</td></tr>
  </tbody>
</table>

<script src="jquery.min.js"></script>
<link type="text/css" rel="stylesheet" href="jquery.firework.css">
<script type="text/javascript" src="jquery.firework.js"></script>
<script>
  $(document).ready(function() {
    loadSnapshots();
  });

  function loadSnapshots() {
    $.ajax("get-databases.cgi", {
      success: function(data) {
        if (Array.isArray(data.databases) && data.databases.length > 0 && data.databases[data.databases.length - 1] === null) {
          data.databases.pop(); // Remove trailing null
        }
        
        var tbody = $("#snapshots-body");
        tbody.empty();
        
        if (data.databases.length === 0) {
          tbody.append('<tr><td colspan="4">No snapshots available</td></tr>');
          return;
        }
        
        for (var i = data.databases.length - 1; i >= 0; i--) {
          var db = data.databases[i];
          var name = db.name.replace("/database/duc_", "").replace(".db", "");
          var displayName = name.replace("_", " ").split(" ");
          var title = displayName[0] + " " + displayName[1].split("_")[0].replaceAll("-", ":");
          
          var sizeText = formatSize(db.size);
          var dbSizeText = formatSize(db['db-size']);
          
          var row = '<tr>' +
            '<td>' + title + '</td>' +
            '<td>' + sizeText + '</td>' +
            '<td>' + dbSizeText + '</td>' +
            '<td><button class="btn btn-danger" onclick="confirmDelete(\'' + db.name + '\', \'' + title + '\')">Delete</button></td>' +
            '</tr>';
          tbody.append(row);
        }
      },
      error: function(xhr, status, error) {
        $("#snapshots-body").html('<tr><td colspan="4">Error loading snapshots: ' + error + '</td></tr>');
        firework.launch('Failed to load snapshots', 'danger', 3000);
      }
    });
  }

  function formatSize(bytes) {
    if (bytes > 1024*1024*1024) {
      return (Math.round(bytes * 10 / 1024 / 1024 / 1024) / 10) + ' GB';
    } else if (bytes > 1024*1024) {
      return (Math.round(bytes * 10 / 1024 / 1024) / 10) + ' MB';
    } else if (bytes > 1024) {
      return (Math.round(bytes * 10 / 1024) / 10) + ' KB';
    } else if (bytes > 0) {
      return bytes + ' B';
    }
    return 'Unknown';
  }

  var pendingAction = null;
  var pendingData = null;

  function showModal(title, message, type, onConfirm, data) {
    pendingAction = onConfirm;
    pendingData = data;
    $('#modal-title').text(title);
    $('#modal-message').text(message);
    $('#modal-header').removeClass('danger primary').addClass(type);
    $('#modal-confirm-btn').removeClass('btn-danger btn-primary').addClass(type === 'danger' ? 'btn-danger' : 'btn-primary');
    $('#modal-overlay').addClass('active');
  }

  function closeModal() {
    $('#modal-overlay').removeClass('active');
    pendingAction = null;
    pendingData = null;
  }

  function modalConfirm() {
    if (pendingAction) {
      pendingAction(pendingData);
    }
    closeModal();
  }

  function confirmDelete(dbPath, title) {
    showModal(
      'Delete Snapshot',
      'Are you sure you want to delete the snapshot "' + title + '"? This action cannot be undone.',
      'danger',
      deleteSnapshot,
      dbPath
    );
  }

  function deleteSnapshot(dbPath) {
    $.ajax({
      url: "delete-snapshot.cgi",
      method: "POST",
      data: { db: dbPath },
      success: function(response) {
        if (response.success) {
          firework.launch('Snapshot deleted successfully', 'success', 2000);
          loadSnapshots();
        } else {
          firework.launch('Failed to delete: ' + response.error, 'danger', 4000);
        }
      },
      error: function(xhr, status, error) {
        firework.launch('Failed to delete snapshot: ' + error, 'danger', 4000);
      }
    });
  }

  function confirmScan() {
    showModal(
      'Start New Scan',
      'Are you sure you want to start a new scan? This may take a while depending on the size of your storage.',
      'primary',
      startScan,
      null
    );
  }

  function startScan() {
    $.ajax({
      url: "trigger-scan.cgi",
      method: "POST",
      success: function(response) {
        if (response.success) {
          firework.launch(response.message, 'success', 3000);
        } else {
          firework.launch(response.message, 'warning', 3000);
        }
      },
      error: function(xhr, status, error) {
        firework.launch('Failed to trigger scan: ' + error, 'danger', 4000);
      }
    });
  }
</script>

EOF

cat footer.htm
echo "</body></html>"
