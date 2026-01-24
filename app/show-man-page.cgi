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

cat header.htm | sed 's/>Snapshot</>DUC Manual</'

cat <<EOF
<style>
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
#content {
  height: 100% - 50px;
  padding: 0;
}
.manual-frame {
  width: 100%;
  height: 100vh;
  border: none;
  margin: 0;
  padding: 0;
}
</style>
<iframe src="duc.1.htm" class="manual-frame"></iframe>
EOF

cat footer.htm

cat <<EOF
  </body>
</html>
EOF