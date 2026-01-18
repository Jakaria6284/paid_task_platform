"""
Run this script to add missing columns to existing database
"""
from sqlalchemy import text
from app.database import engine

def add_missing_columns():
    with engine.connect() as conn:
        try:
            # Add is_open column to projects table
            print("Adding is_open column to projects table...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS is_open BOOLEAN DEFAULT TRUE
            """))
            conn.commit()
            print("✓ is_open column added successfully")
            
            # Add expected_hourly_rate column
            print("\nAdding expected_hourly_rate column to projects table...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS expected_hourly_rate DOUBLE PRECISION DEFAULT 50.0
            """))
            conn.commit()
            print("✓ expected_hourly_rate column added successfully")
            
            # Add expected_duration_hours column
            print("\nAdding expected_duration_hours column to projects table...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS expected_duration_hours DOUBLE PRECISION DEFAULT 40.0
            """))
            conn.commit()
            print("✓ expected_duration_hours column added successfully")
            
            # Add tags column (PostgreSQL array)
            print("\nAdding tags column to projects table...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT ARRAY[]::TEXT[]
            """))
            conn.commit()
            print("✓ tags column added successfully")
            
            # Create proposals table if it doesn't exist
            print("\nCreating proposals table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    developer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    cover_letter TEXT NOT NULL,
                    proposed_hourly_rate DOUBLE PRECISION NOT NULL,
                    estimated_hours DOUBLE PRECISION,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ proposals table created successfully")
            
            # Create index on tags for faster searching
            print("\nCreating index on tags...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_projects_tags 
                ON projects USING GIN (tags)
            """))
            conn.commit()
            print("✓ Index on tags created successfully")
            
            print("\n✅ All migrations completed successfully!")
            print("\n📝 Note: Existing projects will have default values:")
            print("   - expected_hourly_rate: 50.0")
            print("   - expected_duration_hours: 40.0")
            print("   - tags: [] (empty)")
            print("   - is_open: true")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_missing_columns()