#!/usr/bin/env bash



echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
 <body>
EOF

cat header.htm | sed 's/Snapshot/Help/'

cat <<EOF
      <p>Copyrght &copy; 2025 by <a href=https://github.com/caco3/storage-analyzer target=_blank>caco3</a></p>
      <p>Based on &nbsp;<a href=https://duc.zevv.nl/ target=_blank alt=Duc><img src=duc.png width=70px style="vertical-align:middle" ></a></p>
      <p>Icon source: <a href="https://www.flaticon.com/free-icon/storage-space_8110605" title="storage space icons" target=_blank>Storage space icons created by Freepik - Flaticon</a></p>
  
  
EOF



cat footer.htm

cat <<EOF
  </body>
</html>
EOF