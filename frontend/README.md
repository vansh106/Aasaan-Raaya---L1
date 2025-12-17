# Frontend - ERP Agentic Chatbot

Modern React + TypeScript frontend for the ERP AI chatbot.

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with backend URL
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to http://localhost:5173

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Features

- **Real-time Chat Interface**: Smooth, responsive chat experience
- **Message History**: View full conversation history
- **API Insights**: See which APIs were used for each response
- **Error Handling**: Clear error messages and retry options
- **Loading States**: Visual feedback during processing
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Modern UI**: Dark theme with Tailwind CSS

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx   # Main chat component
│   │   ├── Header.tsx          # App header
│   │   └── Message.tsx         # Message display
│   ├── types/
│   │   └── index.ts            # TypeScript definitions
│   ├── App.tsx                 # Root component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── public/                     # Static assets
├── index.html                  # HTML template
├── package.json                # Dependencies
├── vite.config.ts             # Vite config
├── tailwind.config.js         # Tailwind config
└── tsconfig.json              # TypeScript config
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons

## Customization

### Styling

Edit `tailwind.config.js` to customize colors:

```js
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      }
    }
  }
}
```

### API Base URL

Change in `.env`:
```env
VITE_API_BASE_URL=https://your-api-domain.com
```

## Building for Production

1. **Build:**
   ```bash
   npm run build
   ```

2. **Preview build locally:**
   ```bash
   npm run preview
   ```

3. **Deploy `dist` folder** to:
   - Vercel
   - Netlify
   - AWS S3
   - Any static hosting

## Deployment Examples

### Vercel

```bash
npm install -g vercel
vercel
```

### Netlify

```bash
npm run build
netlify deploy --prod --dir=dist
```

### Docker

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t erp-chatbot-frontend .
docker run -p 80:80 erp-chatbot-frontend
```

## Troubleshooting

**Build errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**API connection issues:**
- Check VITE_API_BASE_URL in `.env`
- Ensure backend is running
- Check browser console for CORS errors

**Type errors:**
```bash
npm run build
# Fix any TypeScript errors shown
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

The app is optimized for performance:
- Code splitting
- Lazy loading
- Optimized assets
- Efficient re-renders

## Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Keep components small and focused
4. Add proper type definitions
5. Test in multiple browsers


