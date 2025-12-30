# Project Cleanup and Error Fixes

## Tasks to Complete

### 1. Remove Unnecessary Files
- [x] Remove all test_*.py files (root level) ✅ COMPLETED
- [x] Remove all check_*.py files ✅ COMPLETED
- [x] Remove all add_sample_*.py files ✅ COMPLETED
- [x] Remove archive/ folder ✅ COMPLETED
- [x] Remove backend/erp/ folder (duplicate) ✅ COMPLETED
- [x] Remove backend/__pycache__/ folder ✅ COMPLETED
- [x] Remove backend/instance/ folder (if empty) ✅ COMPLETED
- [x] Remove redundant files like gh.zip, .env.example if not needed ✅ COMPLETED

### 2. Clean Backend Directory
- [x] Keep only: server.py, models.py, ml_app.py, schema.sql, data/ (if needed for initial data) ✅ COMPLETED
- [x] Consolidate requirements.txt (remove backend/requirements.txt) ✅ COMPLETED
- [x] Update imports in server.py if needed ✅ COMPLETED

### 3. Database Cleanup
- [x] Ensure database uses real data, not sample JSON ✅ COMPLETED
- [x] Convert all JSON files to SQL database ✅ COMPLETED
- [x] Update server.py to not load sample data automatically ✅ COMPLETED
- [x] Verify all endpoints work with database data ✅ COMPLETED

### 4. Fix Errors
- [x] Test application startup ✅ COMPLETED
- [x] Test login functionality ✅ COMPLETED
- [x] Test dashboard access ✅ COMPLETED
- [x] Fix any import errors ✅ COMPLETED

### 5. Final Organization
- [x] Update .gitignore if needed ✅ COMPLETED
- [x] Ensure clean directory structure ✅ COMPLETED
- [x] Test full application flow ✅ COMPLETED

### 6. CI & Frontend Consistency
- [x] Add GitHub Actions smoke test workflow ✅ COMPLETED
- [x] Add `TESTING.md` with instructions for running tests ✅ COMPLETED
- [x] Convert remaining frontend pages to use `authManager.apiCall` and `authManager.getUser()` ✅ COMPLETED

### 7. Frontend stability fixes
- [x] Ensure `auth.js` is included on all pages that use `authManager` ✅ COMPLETED
- [x] Guard direct `authManager` usage and add fallbacks where necessary ✅ COMPLETED

### 8. Notification System Implementation
- [x] Add Notification model to backend/models.py ✅ COMPLETED
- [x] Update database schema with notifications table ✅ COMPLETED
- [x] Implement notification API endpoints (GET, PATCH, POST) ✅ COMPLETED
- [x] Update frontend notification.html to use real API data ✅ COMPLETED
- [x] Add sample notifications for testing ✅ COMPLETED
- [x] Clean up sample notification script after use ✅ COMPLETED
