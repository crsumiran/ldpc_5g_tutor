# RTL Lab

This is the canonical learner interface for the Verilog cache laboratory. It is a Next.js notebook-style frontend backed by the FastAPI lab API.

## Getting Started

Start the API from the repository root, then start the frontend:

```bash
npm run dev
```

In another terminal:

```bash
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:3000](http://localhost:3000). Next rewrites `/api/*` to the local FastAPI server. Set `BACKEND_INTERNAL_URL` when the API is elsewhere.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

The page creates a local learner session, autosaves authored Verilog files, polls isolated compile/test jobs, and keeps hidden test details server-side.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
