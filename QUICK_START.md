# ⚡ Quick Start Guide

## 🚀 התחלה מהירה (5 דקות)

### שלב 1: Initialize React Project
```bash
cd "/Users/eyalbarash/Local Development/TimeBroWA-GoogleSync"

# Create Vite project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
```

### שלב 2: Install Core Dependencies
```bash
# Routing & State
npm install react-router-dom @tanstack/react-query zustand

# UI & Styling
npm install -D tailwindcss postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react next-themes

# Forms & Validation
npm install react-hook-form zod @hookform/resolvers

# HTTP
npm install axios

# Utils
npm install date-fns

# Dev Dependencies
npm install -D @types/node
```

### שלב 3: Setup Tailwind CSS
```bash
# Initialize Tailwind
npx tailwindcss init -p

# Update tailwind.config.ts
cat > tailwind.config.ts << 'EOF'
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        info: {
          DEFAULT: "hsl(var(--info))",
          foreground: "hsl(var(--info-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        md: "var(--radius)",
        sm: "var(--radius-sm)",
      },
      spacing: {
        '1': 'var(--spacing-1)',
        '2': 'var(--spacing-2)',
        '3': 'var(--spacing-3)',
        '4': 'var(--spacing-4)',
        '5': 'var(--spacing-5)',
        '6': 'var(--spacing-6)',
        '8': 'var(--spacing-8)',
        '10': 'var(--spacing-10)',
        '12': 'var(--spacing-12)',
        '16': 'var(--spacing-16)',
        '20': 'var(--spacing-20)',
        '24': 'var(--spacing-24)',
        '32': 'var(--spacing-32)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
EOF
```

### שלב 4: Setup shadcn/ui
```bash
# Initialize shadcn/ui
npx shadcn-ui@latest init

# Choose options:
# - TypeScript: Yes
# - Style: Default
# - Base color: Slate
# - CSS variables: Yes
# - Tailwind config: Yes
# - Components path: @/components
# - Utils path: @/lib/utils

# Install commonly used components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add form
npx shadcn-ui@latest add select
npx shadcn-ui@latest add checkbox
npx shadcn-ui@latest add label
```

### שלב 5: Update tsconfig.json
```bash
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path Aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
```

### שלב 6: Update vite.config.ts
```bash
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
EOF
```

### שלב 7: Create Basic Structure
```bash
# Create directories
mkdir -p src/{components/{ui,layout,contacts,groups,statistics,common},pages,hooks,services,types,contexts,utils,lib}

# Create .env file
cat > .env << 'EOF'
VITE_API_URL=http://localhost:8080/api
EOF
```

### שלב 8: Copy Backend Files
```bash
# Create backend directory
mkdir -p backend

# Copy Flask project
cp -r "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"/*.py backend/
cp -r "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"/*.db backend/
cp -r "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"/requirements.txt backend/
cp -r "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"/venv backend/
```

### שלב 9: Run the Project
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python web_interface.py

# Terminal 2 - Frontend (in new terminal)
npm run dev
```

---

## 📝 Next Steps

1. ✅ Project initialized
2. ⏳ Copy design system CSS → [See IMPLEMENTATION_PLAN.md]
3. ⏳ Create core components
4. ⏳ Implement API services
5. ⏳ Build pages
6. ⏳ Add features

---

## 🔍 Verification Checklist

- [ ] React app runs on `http://localhost:5173`
- [ ] Backend runs on `http://localhost:8080`
- [ ] Tailwind CSS working
- [ ] shadcn/ui components installed
- [ ] TypeScript compiling without errors
- [ ] Path aliases (@/) working

---

## 🆘 Troubleshooting

### Issue: Port already in use
```bash
# Find and kill process
lsof -ti:5173 | xargs kill -9
lsof -ti:8080 | xargs kill -9
```

### Issue: Module not found
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: TypeScript errors
```bash
# Restart TypeScript server in your IDE
# Or run:
npm run type-check
```

---

## 📚 Documentation

- [Full Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [API Documentation](./README.md#-api-documentation)
- [Design System](../GreenAPI_MCP_972549990001/static/design-system.css)

---

**זמן משוער**: 5-10 דקות
**סטטוס**: ✅ Ready to start development!




















