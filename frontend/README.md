# FairSight Frontend

React 18 + Vite user interface for FairSight.

## What lives here

- App shell, pages, and route guards in `src/`
- Shared UI components in `src/components/`
- API wrappers in `src/services/`
- Unit and component tests in `tests/`

## Local development

From the frontend directory:

```bash
npm install
npm run dev
```

## Testing

```bash
npm test
npx playwright test
```

## Environment variables

- `VITE_API_BASE_URL` — backend API base URL, such as `http://localhost:8000/api/v1`
- `VITE_LOG_LEVEL` — optional logging level

## Render deployment notes

- Use a Render **Static Site**
- Set the build command to `npm ci && npm run build`
- Publish the `dist` directory
- Point `VITE_API_BASE_URL` to the deployed backend URL