default:
  just --list

# Locally serve the package index
serve:
  python -m http.server -d site