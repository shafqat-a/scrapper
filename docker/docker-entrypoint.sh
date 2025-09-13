#!/bin/bash
set -e

# Docker entrypoint script for Web Scrapper CLI
# Provides flexible container startup options

echo "🚀 Starting Web Scrapper CLI Container..."

# Function to wait for database connectivity
wait_for_db() {
    if [ "$POSTGRES_HOST" ]; then
        echo "⏳ Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
        while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
            sleep 1
        done
        echo "✅ PostgreSQL is ready"
    fi

    if [ "$MONGODB_URL" ]; then
        echo "⏳ Waiting for MongoDB..."
        # Extract host and port from MongoDB URL
        MONGO_HOST=$(echo "$MONGODB_URL" | sed -E 's/mongodb:\/\/([^:]+).*/\1/')
        MONGO_PORT=$(echo "$MONGODB_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        while ! nc -z "$MONGO_HOST" "${MONGO_PORT:-27017}"; do
            sleep 1
        done
        echo "✅ MongoDB is ready"
    fi
}

# Function to run workflow validation
validate_workflows() {
    echo "🔍 Validating workflows in /app/workflows..."
    if [ -d "/app/workflows" ]; then
        for workflow in /app/workflows/*.json; do
            if [ -f "$workflow" ]; then
                echo "Validating $(basename "$workflow")..."
                scrapper validate "$workflow" || echo "⚠️  Validation failed for $(basename "$workflow")"
            fi
        done
    else
        echo "ℹ️  No workflows directory found"
    fi
}

# Function to run a single workflow
run_workflow() {
    local workflow_file="$1"
    echo "🏃 Running workflow: $workflow_file"

    if [ ! -f "$workflow_file" ]; then
        echo "❌ Workflow file not found: $workflow_file"
        exit 1
    fi

    scrapper run "$workflow_file"
}

# Function to show available workflows
list_workflows() {
    echo "📋 Available workflows:"
    if [ -d "/app/workflows" ]; then
        find /app/workflows -name "*.json" -exec basename {} \;
    fi
    if [ -d "/app/examples" ]; then
        echo "📋 Example workflows:"
        find /app/examples -name "*.json" -exec basename {} \;
    fi
}

# Main execution logic
case "${1:-}" in
    "wait-and-run")
        wait_for_db
        if [ "$2" ]; then
            run_workflow "$2"
        else
            echo "❌ Please specify a workflow file"
            list_workflows
            exit 1
        fi
        ;;
    "validate")
        validate_workflows
        ;;
    "validate-and-run")
        wait_for_db
        validate_workflows
        if [ "$2" ]; then
            run_workflow "$2"
        else
            echo "ℹ️  No specific workflow specified, validation complete"
        fi
        ;;
    "list")
        list_workflows
        ;;
    "shell")
        echo "🐚 Starting interactive shell..."
        exec /bin/bash
        ;;
    "scrapper")
        # Pass through to scrapper command
        shift
        wait_for_db
        exec scrapper "$@"
        ;;
    *)
        # If first argument looks like a workflow file, run it
        if [[ "$1" == *.json ]]; then
            wait_for_db
            run_workflow "$1"
        else
            # Default: pass all arguments to scrapper
            wait_for_db
            exec scrapper "$@"
        fi
        ;;
esac
