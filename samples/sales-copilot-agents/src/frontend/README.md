# Sales Copilot Agents Frontend

This folder houses a simple starter **Next.js 13** + **Tailwind CSS** frontend that communicates with your existing backend at `http://localhost:8000`. It’s set up to be deployed in multiple ways:

1. **Local Development**  
   - Ensure [pnpm](https://pnpm.io/) is installed.
   - From within `frontend/`, run:
     ```bash
     pnpm install
     pnpm dev
     ```
   - Visit [http://localhost:3000](http://localhost:3000) to see the app.

2. **Local Docker**  
   - Build the image:
     ```bash
     docker build -t sales-copilot-frontend .
     ```
   - Run the container:
     ```bash
     docker run -p 3000:3000 sales-copilot-frontend
     ```
   - The frontend will be live at [http://localhost:3000](http://localhost:3000).

3. **Static Export** (Optional)  
   If you prefer a static build (note that Next.js 13 features like SSR won’t work in static export), you can:
   ```bash
   pnpm build
   npx next export
