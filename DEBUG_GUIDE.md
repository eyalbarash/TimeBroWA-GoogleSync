# 🐛 TimeBro WhatsApp-Google Sync - Debug Guide

## 🚀 Quick Start

### Start Everything
```bash
# Option 1: Start both servers at once
npm run start:all

# Option 2: Start separately
npm run dev          # Frontend (port 5173)
npm run start:backend # Backend (port 8080)
```

### Debug Status
```bash
npm run debug        # Check server status
```

## 🔍 Debugging Tools

### 1. Server Status Check
```bash
node debug.mjs
```
This will show:
- ✅ Frontend status (React + Vite)
- ✅ Backend status (Python + Flask)
- 📋 Quick access URLs
- 🛠️ Development commands

### 2. Manual Server Checks
```bash
# Check frontend
curl http://localhost:5173

# Check backend
curl http://localhost:8080

# Check backend API
curl http://localhost:8080/api/status
```

### 3. Process Monitoring
```bash
# See running processes
ps aux | grep -E "(vite|python.*web_interface)" | grep -v grep

# Kill processes if needed
pkill -f "vite"
pkill -f "python.*web_interface"
```

## 🛠️ Common Issues & Solutions

### Frontend Issues

#### Blank Page
- **Cause**: Tailwind CSS configuration problems
- **Solution**: 
  ```bash
  npm run dev  # Restart frontend
  ```

#### PostCSS Errors
- **Cause**: Tailwind CSS plugin issues
- **Solution**: 
  ```bash
  npm uninstall @tailwindcss/postcss
  npm run dev
  ```

#### Build Errors
- **Cause**: TypeScript or dependency issues
- **Solution**:
  ```bash
  npm install
  npm run build
  ```

### Backend Issues

#### Module Not Found
- **Cause**: Missing Python dependencies
- **Solution**:
  ```bash
  cd backend
  source venv/bin/activate
  pip install -r requirements.txt
  ```

#### Google API Errors
- **Cause**: Missing Google API packages
- **Solution**:
  ```bash
  cd backend
  source venv/bin/activate
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
  ```

#### Port Already in Use
- **Cause**: Another process using port 8080
- **Solution**:
  ```bash
  lsof -ti:8080 | xargs kill -9
  ```

## 📁 Project Structure

```
TimeBroWA-GoogleSync/
├── src/                    # Frontend (React + TypeScript)
│   ├── components/         # React components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom hooks
│   ├── services/          # API services
│   ├── types/             # TypeScript types
│   ├── contexts/          # React contexts
│   ├── utils/             # Utility functions
│   └── lib/               # Library code
├── backend/               # Backend (Python + Flask)
│   ├── *.py              # Python files
│   ├── *.db              # Database files
│   ├── requirements.txt  # Python dependencies
│   └── venv/             # Virtual environment
├── public/               # Static assets
├── debug.mjs            # Debug script
├── tailwind.config.ts   # Tailwind configuration
├── vite.config.ts       # Vite configuration
└── package.json         # Node.js dependencies
```

## 🌐 URLs

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8080
- **Backend API**: http://localhost:8080/api

## 📝 Development Commands

```bash
# Frontend
npm run dev              # Start development server
npm run build            # Build for production
npm run preview          # Preview production build
npm run lint             # Run ESLint
npm run debug            # Check server status

# Backend
cd backend
source venv/bin/activate
python web_interface.py  # Start Flask server

# Both
npm run start:all        # Start both servers
```

## 🔧 Configuration Files

- `tailwind.config.ts` - Tailwind CSS configuration
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript configuration
- `postcss.config.js` - PostCSS configuration
- `components.json` - shadcn/ui configuration

## 🚨 Emergency Reset

If everything breaks:

```bash
# Stop all processes
pkill -f "vite"
pkill -f "python.*web_interface"

# Clean and reinstall
rm -rf node_modules package-lock.json
npm install

# Restart backend
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Start everything
cd ..
npm run start:all
```

## 📞 Support

If you encounter issues:
1. Run `npm run debug` to check status
2. Check the console for error messages
3. Verify all dependencies are installed
4. Try the emergency reset if needed



















