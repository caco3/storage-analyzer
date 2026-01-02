// Storage Analyzer - Consolidated JavaScript

// Global variables
var snapshots = [];
var db = null;
var path = null;
var selectedIndex = 0;
var selectedScanPaths = [];
var availableScanFolders = [];
var folderDialogExplicit = new Set();
var folderFilter = '';
var pendingAction = null;
var pendingData = null;

// Utility functions
function formatSize(bytes) {
  if (Math.abs(bytes) > 1024*1024*1024*1024) {
    return (Math.round(bytes * 10 / 1024 / 1024 / 1024 / 1024) / 10) + ' TB';
  } else if (Math.abs(bytes) > 1024*1024*1024) {
    return (Math.round(bytes * 10 / 1024 / 1024 / 1024) / 10) + ' GB';
  } else if (Math.abs(bytes) > 1024*1024) {
    return (Math.round(bytes * 10 / 1024 / 1024) / 10) + ' MB';
  } else if (Math.abs(bytes) > 1024) {
    return (Math.round(bytes * 10 / 1024) / 10) + ' KB';
  } else if (Math.abs(bytes) > 0) {
    return bytes + ' B';
  }
  return 'Unknown';
}

function convertUtcToLocal(utcTimestamp) {
  let date;
  
  // Detect format and parse accordingly
  if (utcTimestamp.includes('UTC')) {
    // RFC 2822 format: "Thu Jan  1 22:45:01 UTC 2026"
    date = new Date(utcTimestamp);
  } else if (utcTimestamp.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
    // ISO format: "2026-01-01 22:45:01"
    date = new Date(utcTimestamp + 'Z'); // 'Z' indicates UTC
  } else {
    // Unknown format, return as-is
    return utcTimestamp;
  }
  
  // Format to local time
  return date.getFullYear() + '-' +
    String(date.getMonth() + 1).padStart(2, '0') + '-' +
    String(date.getDate()).padStart(2, '0') + ' ' +
    String(date.getHours()).padStart(2, '0') + ':' +
    String(date.getMinutes()).padStart(2, '0') + ':' +
    String(date.getSeconds()).padStart(2, '0');
}

function convertLocalToUtcHour(localHour) {
  // Get current date to avoid DST issues
  const now = new Date();
  const localDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), localHour, 0, 0);
  const utcDate = new Date(localDate.getTime() + (localDate.getTimezoneOffset() * 60000));
  return utcDate.getHours();
}

function convertUtcToLocalHour(utcHour) {
  // Get current date to avoid DST issues
  const now = new Date();
  const utcDate = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), utcHour, 0, 0));
  return utcDate.getHours();
}

function urlFromIndex(index) {
  if (index < 0 || index >= snapshots.length) {
    firework.launch('Invalid snapshot index', 'danger', 2000);
    index = snapshots.length - 1;
  }
  return 'duc.cgi?cmd=index&db=/snapshots/duc_' + snapshots[index].db + '.db&path=' + path;
}

function urlFromPath(db, p) {
  console.log(db);
  return 'duc.cgi?cmd=index&db=' + db + '&path=' + p;
}

function parseDbName(name) {
  var parts = name.replace('/snapshots/duc_', '').replace('.db', '').replace('_', ' ').split(' ');
  var utcTimestamp = parts[0] + ' ' + parts[1].split('_')[0].replaceAll('-', ':');
  var localTimestamp = convertUtcToLocal(utcTimestamp);
  return {
    db: parts[0] + '_' + parts[1].replaceAll(':', '-'),
    title: localTimestamp
  };
}

// Scan status monitoring
var scanStatusInterval = null;

function startScanStatusMonitoring() {
  // Clear any existing interval
  if (scanStatusInterval) {
    clearInterval(scanStatusInterval);
  }
  
  // Check scan status every 3 seconds
  scanStatusInterval = setInterval(function() {
    $.ajax('get-snapshots.cgi', {
      success: function(data) {
        var oldStatus = window.scanStatus;
        window.scanStatus = data.scan_status || 'idle';
        
        // Update snapshots list if status changed or new snapshots available
        if (oldStatus !== window.scanStatus || data.snapshots.length !== snapshots.length) {
          // Update scan progress indicator
          renderScanProgress();
          
          // Reload snapshots data
          data.snapshots.pop();
          snapshots = [];
          
          data.snapshots.forEach(function(item, i) {
            var parsed = parseDbName(item.name);
            var isSelected = item.name === db;
            if (isSelected) selectedIndex = i;
            
            snapshots.push({
              db: parsed.db,
              title: parsed.title,
              selected: isSelected,
              size: item.size
            });
          });
          
          renderSnapshots();
          
          // Stop monitoring if scan is complete
          if (window.scanStatus === 'idle') {
            clearInterval(scanStatusInterval);
            scanStatusInterval = null;
            firework.launch('Scan completed!', 'success', 3000);
          }
        }
      },
      error: function() {
        // Don't show error for monitoring failures
      }
    });
  }, 3000);
}

function stopScanStatusMonitoring() {
  if (scanStatusInterval) {
    clearInterval(scanStatusInterval);
    scanStatusInterval = null;
  }
}

// Scan progress rendering
function renderScanProgress() {
  var container = $('#scan-progress-container');
  container.empty();
  
  if (window.scanStatus && window.scanStatus !== 'idle') {
    var progressClass = window.scanStatus === 'in_progress' ? 'in-progress' : 'requested';
    var progressText = window.scanStatus === 'in_progress' ? 'Scan in progress...' : 'Scan requested...';
    var progressHtml = '<div class="scan-progress ' + progressClass + '" style="cursor: pointer;" onclick="window.location.href=\'show-log.cgi\'">' +
                      '<div class="scan-progress-icon"></div>' +
                      '<div class="scan-progress-text">' + progressText + '</div>' +
                      '</div>';
    container.html(progressHtml);
  }
}

// Header functions (main page)
function renderSnapshots() {
  var list = $('#snapshots_list');
  list.empty();

  // Reverse the snapshots array to show latest on top
  var reversedSnapshots = snapshots.slice().reverse();
  
  reversedSnapshots.forEach(function(snap, i) {
    var originalIndex = snapshots.length - 1 - i; // Get the original index
    var cls = snap.selected ? 'selected_snapshot' : 'not_selected_snapshot';
    var linkCls = snap.selected ? 'snapshot_link selected_snapshot_link' : 'snapshot_link';
    var sizeText = snap.size > 0 ? ' (' + formatSize(snap.size) + ')' : '';
    
    // Calculate trend compared to previous snapshot
    var trendIndicator = '';
    var trendClass = '';
    if (snap.size > 0 && i < reversedSnapshots.length - 1) {
      var prevSnap = reversedSnapshots[i + 1];
      if (prevSnap && prevSnap.size > 0) {
        var change = snap.size - prevSnap.size;
        var changePercent = (change / prevSnap.size) * 100;
        
        if (change > 0) {
          trendIndicator = ' ↑' + formatSize(change) + ' (+' + changePercent.toFixed(1) + '%)';
          trendClass = 'trend-up';
        } else if (change < 0) {
          trendIndicator = ' ↓' + formatSize(Math.abs(change)) + ' (' + changePercent.toFixed(1) + '%)';
          trendClass = 'trend-down';
        } else {
          trendIndicator = ' → 0%';
          trendClass = 'trend-same';
        }
      }
    }
    
    var li = $('<li class="snapshot"></li>');
    var snapshotUrl = urlFromIndex(originalIndex);
    var content = '<a class="' + linkCls + '" href="' + snapshotUrl + '" style="display: block; width: 100%; height: 100%; text-decoration: none;">' +
                  '<span class="' + cls + '">' + snap.title + sizeText;
    
    if (trendIndicator) {
      content += '<span class="trend-indicator ' + trendClass + '">' + trendIndicator + '</span>';
    }
    
    content += '</span></a>';
    li.html(content);
    list.append(li);
  });

  // Scroll to selected snapshot after rendering
  setTimeout(function() {
    var selectedElement = $('#snapshots_list .selected_snapshot').closest('li');
    if (selectedElement.length > 0) {
      var snapshotsContainer = $('#snapshots');
      var containerHeight = snapshotsContainer.height();
      var elementTop = selectedElement.position().top;
      var elementHeight = selectedElement.outerHeight();
      var scrollTop = elementTop - (containerHeight / 2) + (elementHeight / 2);
      
      snapshotsContainer.scrollTop(scrollTop);
    }
  }, 100);
}

function renderBreadcrumb() {
  var folders = path.split('/');
  var crumbs = '<a class="not_selected_snapshot snapshot_link" href="' + 
               urlFromPath(db, '/scan') + '">/</a>';
  var f = '';
  
  for (var i = 2; i < folders.length; i++) {
    f += folders[i] + '/';
    crumbs += ' <span class="breadcrumb-sep">›</span> <a class="not_selected_snapshot snapshot_link" href="' + 
              urlFromPath(db, '/scan/' + f.slice(0, -1)) + '">' + folders[i] + '</a>';
  }
  
  $('#path').html(crumbs);
}

// Manage snapshots functions
function loadSnapshots() {
  $.ajax("get-snapshots.cgi", {
    success: function(data) {
      if (Array.isArray(data.snapshots) && data.snapshots.length > 0 && data.snapshots[data.snapshots.length - 1] === null) {
        data.snapshots.pop(); // Remove trailing null
      }
      
      var tbody = $("#snapshots-body");
      tbody.empty();
      
      if (data.snapshots.length === 0) {
        tbody.append('<tr><td colspan="4">No snapshots available</td></tr>');
        return;
      }
      
      for (var i = data.snapshots.length - 1; i >= 0; i--) {
        var db = data.snapshots[i];
        var name = db.name.replace("/snapshots/duc_", "").replace(".db", "");
        var displayName = name.replace("_", " ").split(" ");
        var utcTimestamp = displayName[0] + " " + displayName[1].split("_")[0].replaceAll("-", ":");
        var localTimestamp = convertUtcToLocal(utcTimestamp);
        
        var sizeText = formatSize(db.size);
        var dbSizeText = formatSize(db['db-size']);
        
        var row = '<tr>' +
          '<td>' + localTimestamp + '</td>' +
          '<td>' + sizeText + '</td>' +
          '<td>' + dbSizeText + '</td>' +
          '<td><button class="btn btn-danger" onclick="confirmDelete(\'' + db.name + '\', \'' + localTimestamp + '\')">Delete</button></td>' +
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
        // Redirect to log page after successful manual scan
        setTimeout(function() {
          window.location.href = 'show-log.cgi';
        }, 1000);
      } else {
        firework.launch(response.message, 'warning', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to trigger scan: ' + error, 'danger', 4000);
    }
  });
}

// Configuration functions
function showStatus(message, type) {
  var statusClass = 'actions-section';
  if (type === 'success') {
    statusClass = 'actions-section';
    $('#status-message').html('<div class="' + statusClass + ' status-success">' + message + '</div>');
  } else if (type === 'error') {
    statusClass = 'actions-section';
    $('#status-message').html('<div class="' + statusClass + ' status-error">' + message + '</div>');
  } else if (type === 'warning') {
    statusClass = 'actions-section';
    $('#status-message').html('<div class="' + statusClass + ' status-warning">' + message + '</div>');
  }
  setTimeout(function() {
    $('#status-message').html('');
  }, 5000);
}

function loadExclude() {
  $.ajax({
    url: "get-exclude.cgi",
    method: "GET",
    success: function(resp) {
      if (resp && resp.success) {
        $('#exclude-input').val(resp.exclude || '');
      } else {
        firework.launch('Failed to load exclude patterns', 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to load exclude patterns: ' + error, 'danger', 3000);
    }
  });
}

function confirmSaveExclude() {
  var exclude = ($('#exclude-input').val() || '').trim();
  showModal(
    'Update Exclude Patterns',
    'Save exclude patterns?<br><br><strong>' + exclude + '</strong><br><br>This affects scheduled and manual scans.',
    'primary',
    saveExclude,
    exclude
  );
}

function saveExclude(exclude) {
  $.ajax({
    url: "set-exclude.cgi",
    method: "POST",
    data: { exclude: exclude },
    success: function(resp) {
      if (resp && resp.success) {
        firework.launch('Exclude patterns updated', 'success', 3000);
        $('#exclude-input').val(resp.exclude || exclude);
      } else {
        firework.launch('Failed to update exclude patterns: ' + (resp && resp.error ? resp.error : 'unknown error'), 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to update exclude patterns: ' + error, 'danger', 3000);
    }
  });
}

function loadDucParams() {
  $.ajax({
    url: "get-duc-params.cgi",
    method: "GET",
    success: function(resp) {
      if (resp && resp.success) {
        $('#check-hard-links').val(resp.check_hard_links || 'yes');
        $('#max-depth').val(resp.max_depth || '5');
      } else {
        firework.launch('Failed to load DUC parameters', 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to load DUC parameters: ' + error, 'danger', 3000);
    }
  });
}

function confirmSaveDucParams() {
  var checkHardLinks = $('#check-hard-links').val();
  var maxDepth = $('#max-depth').val();
  
  var message = 'Save DUC parameters?\n\n';
  message += 'Check Hard Links: ' + (checkHardLinks === 'yes' ? 'Yes (count hard links once)' : 'No (count hard links separately)') + '\n';
  message += 'Max Depth: ' + maxDepth + ' levels\n\n';
  message += 'This affects how scans are performed.';
  
  showModal(
    'Update DUC Parameters',
    message,
    'primary',
    saveDucParams,
    { check_hard_links: checkHardLinks, max_depth: maxDepth }
  );
}

function saveDucParams(params) {
  $.ajax({
    url: "set-duc-params.cgi",
    method: "POST",
    data: {
      check_hard_links: params.check_hard_links,
      max_depth: params.max_depth
    },
    success: function(resp) {
      if (resp && resp.success) {
        firework.launch('DUC parameters updated', 'success', 3000);
      } else {
        firework.launch('Failed to update DUC parameters: ' + (resp && resp.error ? resp.error : 'unknown error'), 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to update DUC parameters: ' + error, 'danger', 3000);
    }
  });
}

function loadSchedule() {
  $.ajax({
    url: "get-schedule.cgi",
    method: "GET",
    success: function(resp) {
      if (resp && resp.success) {
        if (resp.supported) {
          $('#schedule-unsupported').hide();
          $('#schedule-mode').val(resp.mode);
          $('#schedule-minute').val(resp.minute);
          
          // Convert UTC hour to local hour for display
          var localHour = convertUtcToLocalHour(resp.hour);
          $('#schedule-hour').val(localHour);
          
          $('#schedule-dow').val(resp.dow);
          $('#schedule-dom').val(resp.dom);
        } else {
          $('#schedule-unsupported').show();
        }
        updateScheduleFieldsVisibility();
        updateSchedulePreview();
      } else {
        firework.launch('Failed to load schedule', 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to load schedule: ' + error, 'danger', 3000);
    }
  });
}

function bindScheduleUI() {
  $('#schedule-mode').on('change', function() {
    updateScheduleFieldsVisibility();
    updateSchedulePreview();
  });
  $('#schedule-minute, #schedule-hour, #schedule-dom').on('input', updateSchedulePreview);
  $('#schedule-dow').on('change', updateSchedulePreview);
  updateScheduleFieldsVisibility();
  updateSchedulePreview();
}

function updateScheduleFieldsVisibility() {
  var mode = $('#schedule-mode').val();
  var showHour = (mode === 'daily' || mode === 'weekly' || mode === 'monthly');
  var showDow = (mode === 'weekly');
  var showDom = (mode === 'monthly');

  $('#schedule-hour').prop('disabled', !showHour);
  $('#schedule-dow').prop('disabled', !showDow);
  $('#schedule-dom').prop('disabled', !showDom);
}

function updateSchedulePreview() {
  var mode = $('#schedule-mode').val();
  var minute = parseInt($('#schedule-minute').val() || '0', 10);
  var localHour = parseInt($('#schedule-hour').val() || '0', 10);
  var dow = $('#schedule-dow').val();
  var dom = parseInt($('#schedule-dom').val() || '1', 10);

  // Convert local hour to UTC for cron
  var utcHour = convertLocalToUtcHour(localHour);

  var cron = '';
  if (mode === 'hourly') {
    cron = minute + ' * * * *';
  } else if (mode === 'daily') {
    cron = minute + ' ' + utcHour + ' * * *';
  } else if (mode === 'weekly') {
    cron = minute + ' ' + utcHour + ' * * ' + dow;
  } else if (mode === 'monthly') {
    cron = minute + ' ' + utcHour + ' ' + dom + ' * *';
  }

  $('#schedule-preview').text('Cron: ' + cron);
  $('#schedule-cron').text(cron);
  // Update button tooltip with current cron expression
  $('button[onclick="confirmSaveSchedule()"]').attr('title', 'Cron configuration: ' + cron);
}

function confirmSaveSchedule() {
  var mode = $('#schedule-mode').val();
  var minute = parseInt($('#schedule-minute').val() || '0', 10);
  var localHour = parseInt($('#schedule-hour').val() || '0', 10);
  var dow = parseInt($('#schedule-dow').val() || '1', 10);
  var dom = parseInt($('#schedule-dom').val() || '1', 10);

  if (isNaN(minute) || minute < 0 || minute > 59) {
    showStatus('Minute must be between 0 and 59', 'error');
    return;
  }
  if ((mode === 'daily' || mode === 'weekly' || mode === 'monthly') && (isNaN(localHour) || localHour < 0 || localHour > 23)) {
    showStatus('Hour must be between 0 and 23', 'error');
    return;
  }
  if (mode === 'weekly' && (isNaN(dow) || dow < 0 || dow > 6)) {
    showStatus('Day of week must be between 0 and 6', 'error');
    return;
  }
  if (mode === 'monthly' && (isNaN(dom) || dom < 1 || dom > 31)) {
    showStatus('Day of month must be between 1 and 31', 'error');
    return;
  }

  // Convert local hour to UTC for server
  var utcHour = convertLocalToUtcHour(localHour);

  // Generate cron expression and human readable text
  var cron = '';
  var humanReadable = '';
  
  if (mode === 'hourly') {
    cron = minute + ' * * * *';
    humanReadable = 'Every hour at minute ' + minute;
  } else if (mode === 'daily') {
    cron = minute + ' ' + utcHour + ' * * *';
    humanReadable = 'Every day at ' + localHour.toString().padStart(2, '0') + ':' + minute.toString().padStart(2, '0');
  } else if (mode === 'weekly') {
    cron = minute + ' ' + utcHour + ' * * ' + dow;
    var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    humanReadable = 'Every ' + days[dow] + ' at ' + localHour.toString().padStart(2, '0') + ':' + minute.toString().padStart(2, '0');
  } else if (mode === 'monthly') {
    cron = minute + ' ' + utcHour + ' ' + dom + ' * *';
    humanReadable = 'Every month on day ' + dom + ' at ' + localHour.toString().padStart(2, '0') + ':' + minute.toString().padStart(2, '0');
  }
  
  var displayText = humanReadable + '<br><small>(Cron configuration: ' + cron + ')</small>';
  
  showModal(
    'Update Schedule',
    'Save the new schedule?<br><br><strong>' + displayText + '</strong><br><br>This controls when automatic scans run.',
    'primary',
    saveSchedule,
    { mode: mode, minute: minute, hour: utcHour, dow: dow, dom: dom, preview: cron }
  );
}

function saveSchedule(payload) {
  $.ajax({
    url: "set-schedule.cgi",
    method: "POST",
    data: {
      mode: payload.mode,
      minute: payload.minute,
      hour: payload.hour,
      dow: payload.dow,
      dom: payload.dom
    },
    success: function(resp) {
      if (resp && resp.success) {
        firework.launch('Schedule updated', 'success', 3000);
        $('#schedule-unsupported').hide();
        $('#schedule-preview').text('Cron: ' + (resp.schedule || payload.preview));
  // Update button tooltip with saved cron expression
  $('button[onclick="confirmSaveSchedule()"]').attr('title', 'Current schedule: ' + (resp.schedule || payload.preview));
      } else {
        firework.launch('Failed to update schedule: ' + (resp && resp.error ? resp.error : 'unknown error'), 'danger', 3000);
      }
    },
    error: function(xhr, status, error) {
      firework.launch('Failed to update schedule: ' + error, 'danger', 3000);
    }
  });
}

// Modal functions
function showModal(title, message, type, onConfirm, data) {
  pendingAction = onConfirm;
  pendingData = data;
  $('#modal-title').text(title);
  $('#modal-message').html(message);
  $('#modal-header').removeClass('danger primary').addClass(type);
  $('#modal-confirm-btn').removeClass('btn-danger btn-primary').addClass(type === 'danger' ? 'btn-danger' : 'btn-primary');
  $('#modal-overlay').show();
}

function closeModal() {
  $('#modal-overlay').hide();
  pendingAction = null;
  pendingData = null;
}

function modalConfirm() {
  if (pendingAction) {
    pendingAction(pendingData);
  }
  closeModal();
}

// Error page functions
function handleDbError() {
  /* Check if the db parameter is provided in the URL and use it */
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  var db = "";
  if (urlParams.has('db')) {
      db = urlParams.get('db');
      console.log("DB: " + db);
      //db = db.replace("/snapshots", "");
  }
  
  document.getElementById("db_error").innerHTML = db;
}

function handlePathError() {
  /* Check if the path parameter is provided in the URL and use it */
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  var path = "";
  if (urlParams.has('path')) {
      path = urlParams.get('path');
      console.log("path: " + path);
  }
  
  document.getElementById("path_error").innerHTML = path;

  var db = "";
  if (urlParams.has('db')) {
      db = urlParams.get('db');
      console.log("DB: " + db);
  }

  document.getElementById("folder_up_button").href = "duc.cgi?db=" + db + "&cmd=index&path=" + path.split("/").slice(0, -1).join("/")
}

// Main initialization
$(document).ready(function() {
  // Check which page we're on and initialize accordingly
  var url = new URL(location.href);
  var pathname = url.pathname;
  
  // Header/main page initialization
  if (pathname.includes('duc.cgi') || pathname.includes('/')) {
    var showSidebar = url.href.indexOf('duc.cgi') !== -1 || 
                      url.href.indexOf('/?db') !== -1 || 
                      url.href.indexOf('error.cgi') !== -1;

    if (showSidebar) {
      $('#main_sidebar').show();
    }

    // Handle scroll to hide/show keyboard shortcuts
    var lastScrollTop = 0;
    var scrollThreshold = 50;
    
    $('#snapshots').on('scroll', function() {
      var scrollTop = $(this).scrollTop();
      var shortcuts = $('#keyboard-shortcuts');
      
      if (scrollTop > scrollThreshold) {
        shortcuts.addClass('hidden');
      } else {
        shortcuts.removeClass('hidden');
      }
      
      lastScrollTop = scrollTop;
    });

    $.ajax('get-snapshots.cgi', {
      success: function(data) {
        data.snapshots.pop();

        // Store scan status globally
        window.scanStatus = data.scan_status || 'idle';

        // Render scan progress indicator
        renderScanProgress();

        if (data.snapshots.length === 0) {
          snapshots = [];
          db = null;
          path = '/scan';
          $('#snapshots_list').html('<li class="snapshot"><span class="not_selected_snapshot">No snapshots yet</span></li>');
          $('#path').html('');
          return;
        }
        
        db = url.searchParams.get('db');
        if (!db && data.snapshots.length > 0) {
          db = data.snapshots[data.snapshots.length - 1]['db'];
        }

        path = url.searchParams.get('path') || '/scan';

        data.snapshots.forEach(function(item, i) {
          var parsed = parseDbName(item.name);
          var isSelected = item.name === db;
          if (isSelected) selectedIndex = i;
          
          snapshots.push({
            db: parsed.db,
            title: parsed.title,
            selected: isSelected,
            size: item.size
          });
        });

        if (db) {
          renderSnapshots();
          renderBreadcrumb();
        }

        // Set up auto-refresh if scan is in progress
        if (window.scanStatus === 'in_progress' || window.scanStatus === 'requested') {
          startScanStatusMonitoring();
        }
      },
      error: function(xhr, status, error) {
        firework.launch('Failed to load snapshots: ' + error, 'danger', 5000);
        $('#snapshots').html('<p class="error">Failed to load snapshots</p>');
      }
    });

    $(document).on('keypress', function(e) {
      var key = e.key.toLowerCase();

      if (snapshots.length === 0) {
        if (key === 'n' || key === 'p') {
          firework.launch('No snapshots available', 'warning', 2000);
        }
        return;
      }
      
      if (key === 'p' && selectedIndex > 0) {
        window.location.href = urlFromIndex(selectedIndex - 1);
      } else if (key === 'p') {
        firework.launch('Already at oldest snapshot', 'success', 1500);
      } else if (key === 'n' && selectedIndex < snapshots.length - 1) {
        window.location.href = urlFromIndex(selectedIndex + 1);
      } else if (key === 'n') {
        firework.launch('Already at latest snapshot', 'success', 1500);
      }
    });
  }
  
  // Manage snapshots page initialization
  if (pathname.includes('manage-snapshots.cgi')) {
    loadSnapshots();
  }
  
  // Configuration page initialization
  if (pathname.includes('config.cgi')) {
    loadExclude();
    loadDucParams();
    loadSchedule();
    bindScheduleUI();
  }
  
  // Error page initialization
  if (pathname.includes('db-error.cgi')) {
    handleDbError();
  }
  
  if (pathname.includes('path-error.cgi')) {
    handlePathError();
  }
  
  // Trend page initialization
  if (pathname.includes('trend.cgi')) {
    initializeTrendPage();
  }
  
  // Log page initialization
  if (pathname.includes('show-log.cgi')) {
    // Convert initial log content to local time
    const logDisplay = document.getElementById('log-display');
    if (logDisplay) {
      logDisplay.innerHTML = convertLogUtcToLocal(logDisplay.innerHTML);
    }
    // Start auto-reload
    setInterval(reloadLog, 1000);
  }
});

// Trend page functions
function initializeTrendPage() {
  loadTrendData();
  
  $('#refresh-trend').click(loadTrendData);
  $('#trend-period').change(loadTrendData);
}

function loadTrendData() {
  const period = $('#trend-period').val();
  
  // Show loading state
  $('#trend-chart-container').html('<div class="chart-placeholder"><p>Loading trend data...</p><div class="loading-spinner"></div></div>');
  $('#trend-data-table tbody').html('<tr><td colspan="4" class="loading-row">Loading data...</td></tr>');
  
  // Fetch real data from server
  $.ajax({
    url: 'get-trend-data.cgi',
    method: 'GET',
    dataType: 'json',
    success: function(data) {
      const filteredData = filterDataByPeriod(data.snapshots, period);
      updateTrendChart(filteredData);
      updateTrendStats(filteredData);
      updateTrendTable(filteredData);
    },
    error: function(xhr, status, error) {
      $('#trend-chart-container').html('<div class="chart-placeholder"><p>Error loading data: ' + error + '</p></div>');
      $('#trend-data-table tbody').html('<tr><td colspan="4" class="loading-row">Error loading data</td></tr>');
    }
  });
}

function filterDataByPeriod(snapshots, period) {
  if (!snapshots || snapshots.length === 0) return [];
  
  const now = new Date();
  let cutoffDate = new Date();
  
  if (period === 'all') {
    return snapshots;
  } else {
    const days = parseInt(period);
    cutoffDate.setDate(now.getDate() - days);
  }
  
  return snapshots.filter(snapshot => {
    const snapshotDate = new Date(snapshot.timestamp);
    return snapshotDate >= cutoffDate;
  });
}

function updateTrendChart(data) {
  if (!data || data.length === 0) {
    $('#trend-chart-container').html('<div class="chart-placeholder"><p>No data available for selected period</p></div>');
    return;
  }
  
  const chartHtml = `
    <div class="simple-chart">
      <div class="chart-bars">
        ${data.map((point, index) => {
          const maxSize = Math.max(...data.map(d => d.size));
          const height = (point.size / maxSize) * 200;
          const dateLabel = point.date ? point.date.split('-').slice(1).join('/') : '';
          const sizeLabel = formatSize(point.size);
          const localTimestamp = convertUtcToLocal(point.timestamp);
          return `
            <div class="chart-bar clickable-bar" style="height: ${height}px;" 
                 title="${localTimestamp}: ${sizeLabel}"
                 data-snapshot="${point.filename}"
                 onclick="navigateToSnapshot('${point.filename}')">
              <div class="bar-size-label">${sizeLabel}</div>
              <div class="bar-label">${dateLabel}</div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
  
  $('#trend-chart-container').html(chartHtml);
}

function navigateToSnapshot(filename) {
  // Extract database name from filename (remove .db extension if present)
  const dbName = filename.replace('.db', '');
  // Navigate to the main view with this snapshot
  window.location.href = `duc.cgi?cmd=index&db=/snapshots/${dbName}.db&path=/scan`;
}

function updateTrendStats(data) {
  if (!data || data.length < 2) {
    $('#current-size').text('--');
    $('#growth-rate').text('--');
    $('#avg-daily-growth').text('--');
    return;
  }
  
  const current = data[data.length - 1];
  const previous = data[data.length - 2];
  const oldest = data[0];
  
  const totalGrowth = current.size - oldest.size;
  const daysDiff = Math.ceil((new Date(current.timestamp) - new Date(oldest.timestamp)) / (1000 * 60 * 60 * 24));
  const avgDailyGrowth = daysDiff > 0 ? totalGrowth / daysDiff : 0;
  const growthRate = previous.size > 0 ? ((current.size - previous.size) / previous.size * 100) : 0;
  
  $('#current-size').text(formatSize(current.size));
  $('#growth-rate').text(growthRate.toFixed(2) + '%');
  $('#avg-daily-growth').text(formatSize(avgDailyGrowth) + '/day');
}

function updateTrendTable(data) {
  if (!data || data.length === 0) {
    $('#trend-data-table tbody').html('<tr><td colspan="4" class="loading-row">No data available</td></tr>');
    return;
  }
  
  const tableRows = data.slice().reverse().map((point, index) => {
    const change = index < data.length - 1 ? point.size - data[data.length - 2 - index].size : 0;
    const changePercent = index < data.length - 1 && data[data.length - 2 - index].size > 0 
      ? (change / data[data.length - 2 - index].size * 100) 
      : 0;
    
    const changeClass = change > 0 ? 'change-positive' : change < 0 ? 'change-negative' : '';
    const changeText = change > 0 ? '+' + formatSize(change) : change < 0 ? formatSize(change) : '--';
    const changePercentText = changePercent > 0 ? '+' + changePercent.toFixed(2) + '%' : 
                             changePercent < 0 ? changePercent.toFixed(2) + '%' : '--';
    
    // Convert UTC timestamp to local time
    const localTimestamp = convertUtcToLocal(point.timestamp);
    
    return `
      <tr>
        <td>${localTimestamp}</td>
        <td>${formatSize(point.size)}</td>
        <td class="${changeClass}">${changeText}</td>
        <td class="${changeClass}">${changePercentText}</td>
      </tr>
    `;
  }).join('');
  
  $('#trend-data-table tbody').html(tableRows);
}

// Log page functions
function convertLogUtcToLocal(logContent) {
  return logContent.replace(/^([A-Z][a-z]{2} [A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2} UTC \d{4})(.*)$/gm, function(match, utcTime, rest) {
    const localTime = convertUtcToLocal(utcTime);
    return localTime + rest;
  });
}

function reloadLog() {
  fetch('show-log.cgi?content=only')
    .then(response => response.text())
    .then(data => {
      const localData = convertLogUtcToLocal(data);
      document.getElementById('log-display').innerHTML = localData;
    })
    .catch(error => console.error('Error reloading log:', error));
}
