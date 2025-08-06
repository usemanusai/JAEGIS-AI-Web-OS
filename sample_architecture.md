
# Sample Web Application Architecture

## Project Overview
Build a modern web application using Next.js, React, and TypeScript.

## Technology Stack
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- Prisma ORM
- SQLite Database

## Setup Instructions

### Initialize Project
npx create-next-app@latest my-app --typescript --tailwind --eslint --app
cd my-app

### Install Dependencies
npm install prisma @prisma/client
npm install zustand framer-motion lucide-react
npm install -D @types/node

### Database Setup
npx prisma init --datasource-provider sqlite
npx prisma generate
npx prisma db push

### File Structure
src/
  app/
    layout.tsx
    page.tsx
    globals.css
  components/
    ui/
  lib/
    db.ts
    utils.ts

## Configuration Files

### package.json
{
  "name": "my-app",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}

### Database Schema
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}

model User {
  id    String @id @default(cuid())
  email String @unique
  name  String?
}

## Build Commands
npm run build
npm run start
