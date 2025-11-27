#!/bin/bash

# Script to setup production database and run migrations

set -e

echo "🚀 Setting up Agape V3 Production Environment"
echo "=============================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 1: Create database
echo "📊 Step 1: Creating database in Aurora..."
python create_database.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to create database. Please check:"
    echo "  1. Aurora security group allows your IP"
    echo "  2. Aurora is publicly accessible (if connecting from outside VPC)"
    echo "  3. Database credentials are correct"
    exit 1
fi
echo ""

# Step 2: Create initial migration
echo "📝 Step 2: Creating initial Alembic migration..."
alembic revision --autogenerate -m "Initial migration - users table"
echo ""

# Step 3: Apply migrations
echo "⬆️  Step 3: Applying migrations to Aurora..."
alembic upgrade head
echo ""

# Step 4: Verify setup
echo "✅ Step 4: Verifying setup..."
python -c "
import asyncio
from app.infrastructure.database import db

async def test_connection():
    db.initialize()
    async for session in db.get_session():
        print('✓ Database connection successful!')
        break
    await db.close()

asyncio.run(test_connection())
"
echo ""

echo "✅ Production setup complete!"
echo ""
echo "To start the application:"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or with auto-reload for development:"
echo "  uvicorn app.main:app --reload"
