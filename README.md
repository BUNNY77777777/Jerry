# Jerry - AI Executive Agent Monorepo

## Overview
Jerry is an AI executive assistant / chief-of-staff built with:
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI, LangGraph, Supabase (`pgvector`), Google Gemini
- **Database**: Supabase PostgreSQL with `pgvector` for semantic long-term memory and governance audit trails.

## Directory Structure
```
Jerry/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── governance/
│   │   ├── jerry_agent/
│   │   ├── mcp_tools/
│   │   ├── memory/
│   │   └── schemas/
│   ├── .env.example
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── globals.css
│   │       ├── layout.tsx
│   │       └── page.tsx
│   ├── .env.example
│   ├── next.config.js
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── supabase_schema.sql
└── vercel.json
```
