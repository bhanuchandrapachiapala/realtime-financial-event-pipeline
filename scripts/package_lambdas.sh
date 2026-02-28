#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDAS_DIR="$PROJECT_ROOT/lambdas"

echo "Packaging Lambda functions from $LAMBDAS_DIR"
echo "---"

for LAMBDA_DIR in "$LAMBDAS_DIR"/*/; do
  [ -d "$LAMBDA_DIR" ] || continue
  NAME="$(basename "$LAMBDA_DIR")"
  echo "Packaging $NAME..."

  STAGE="$(mktemp -d)"
  cp "$LAMBDA_DIR"/*.py "$STAGE/" 2>/dev/null || true
  if [ ! -f "$STAGE/lambda_function.py" ]; then
    echo "  Skipping $NAME: no lambda_function.py found"
    rm -rf "$STAGE"
    continue
  fi

  if [ -f "$LAMBDA_DIR/requirements.txt" ] && [ -s "$LAMBDA_DIR/requirements.txt" ]; then
    echo "  Installing dependencies from requirements.txt..."
    pip install -q -r "$LAMBDA_DIR/requirements.txt" -t "$STAGE"
  else
    echo "  No requirements.txt or empty — skipping dependency install"
  fi

  echo "  Creating package.zip..."
  (cd "$STAGE" && zip -r -q package.zip . -x "*.pyc" -x "*__pycache__*")
  mv "$STAGE/package.zip" "$LAMBDA_DIR/package.zip"
  rm -rf "$STAGE"

  echo "  Done: $LAMBDA_DIR/package.zip"
  echo "---"
done

echo "All Lambda packages built."
