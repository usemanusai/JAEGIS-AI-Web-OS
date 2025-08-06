"""
Next.js Project Template

Generates complete Next.js applications with TypeScript, Tailwind CSS,
and modern development setup.
"""

from typing import Dict, List
from .base_template import BaseTemplate, ProjectStructure, FileTemplate, create_package_json_content, create_gitignore_content, create_readme_content


class NextJSTemplate(BaseTemplate):
    """Template for Next.js projects."""
    
    def get_framework_name(self) -> str:
        return "Next.js"
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return Next.js dependencies."""
        return {
            'runtime': [
                'next@latest',
                'react@latest', 
                'react-dom@latest',
                '@types/node@latest',
                '@types/react@latest',
                '@types/react-dom@latest',
                'typescript@latest'
            ],
            'development': [
                'eslint@latest',
                'eslint-config-next@latest',
                'tailwindcss@latest',
                'postcss@latest',
                'autoprefixer@latest'
            ]
        }
    
    def get_project_structure(self) -> ProjectStructure:
        """Return Next.js project structure."""
        
        # Dependencies
        deps = self.get_dependencies()
        dependencies = {dep.split('@')[0]: dep.split('@')[1] if '@' in dep else 'latest' 
                       for dep in deps['runtime']}
        dev_dependencies = {dep.split('@')[0]: dep.split('@')[1] if '@' in dep else 'latest' 
                           for dep in deps['development']}
        
        # Scripts
        scripts = {
            "dev": "next dev",
            "build": "next build", 
            "start": "next start",
            "lint": "next lint"
        }
        
        # Files
        files = [
            # Package.json
            FileTemplate(
                path="package.json",
                content=create_package_json_content(
                    self.project_name, dependencies, dev_dependencies, scripts
                ),
                is_template=False
            ),
            
            # Next.js config
            FileTemplate(
                path="next.config.js",
                content=self._get_next_config_content()
            ),
            
            # TypeScript config
            FileTemplate(
                path="tsconfig.json",
                content=self._get_tsconfig_content()
            ),
            
            # Tailwind config
            FileTemplate(
                path="tailwind.config.js",
                content=self._get_tailwind_config_content()
            ),
            
            # PostCSS config
            FileTemplate(
                path="postcss.config.js",
                content=self._get_postcss_config_content()
            ),
            
            # App layout
            FileTemplate(
                path="src/app/layout.tsx",
                content=self._get_layout_content()
            ),
            
            # App page
            FileTemplate(
                path="src/app/page.tsx", 
                content=self._get_page_content()
            ),
            
            # Global styles
            FileTemplate(
                path="src/app/globals.css",
                content=self._get_global_css_content()
            ),
            
            # Components
            FileTemplate(
                path="src/components/ui/Button.tsx",
                content=self._get_button_component_content()
            ),
            
            # Lib utilities
            FileTemplate(
                path="src/lib/utils.ts",
                content=self._get_utils_content()
            ),
            
            # Environment example
            FileTemplate(
                path=".env.example",
                content=self._get_env_example_content()
            ),
            
            # Gitignore
            FileTemplate(
                path=".gitignore",
                content=create_gitignore_content([
                    "# Dependencies",
                    "node_modules/",
                    "",
                    "# Next.js",
                    ".next/",
                    "out/",
                    "",
                    "# Environment variables",
                    ".env.local",
                    ".env.development.local", 
                    ".env.test.local",
                    ".env.production.local",
                    "",
                    "# Logs",
                    "npm-debug.log*",
                    "yarn-debug.log*",
                    "yarn-error.log*",
                    "",
                    "# IDE",
                    ".vscode/",
                    ".idea/"
                ]),
                is_template=False
            ),
            
            # README
            FileTemplate(
                path="README.md",
                content=create_readme_content(
                    self.project_name,
                    f"A modern Next.js application built with TypeScript and Tailwind CSS.",
                    [
                        "Install dependencies: `npm install`",
                        "Start development server: `npm run dev`",
                        "Open http://localhost:3000 in your browser"
                    ]
                ),
                is_template=False
            )
        ]
        
        return ProjectStructure(
            directories=[
                "src",
                "src/app",
                "src/components",
                "src/components/ui", 
                "src/lib",
                "public"
            ],
            files=files,
            dependencies=deps,
            scripts=scripts,
            environment_variables={}
        )
    
    def _get_next_config_content(self) -> str:
        return """/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: [],
  },
}

module.exports = nextConfig"""
    
    def _get_tsconfig_content(self) -> str:
        return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""
    
    def _get_tailwind_config_content(self) -> str:
        return """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}"""
    
    def _get_postcss_config_content(self) -> str:
        return """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
    
    def _get_layout_content(self) -> str:
        return """import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '{{ project_name }}',
  description: 'Generated by MCP Server',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}"""
    
    def _get_page_content(self) -> str:
        return """import { Button } from '@/components/ui/Button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          Welcome to&nbsp;
          <code className="font-mono font-bold">{{ project_name }}</code>
        </p>
      </div>

      <div className="relative flex place-items-center">
        <h1 className="text-4xl font-bold text-center">
          {{ project_name }}
        </h1>
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-4 lg:text-left">
        <Button className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30">
          Get Started
        </Button>
      </div>
    </main>
  )
}"""
    
    def _get_global_css_content(self) -> str:
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

@media (prefers-color-scheme: dark) {
  :root {
    --foreground-rgb: 255, 255, 255;
    --background-start-rgb: 0, 0, 0;
    --background-end-rgb: 0, 0, 0;
  }
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}"""
    
    def _get_button_component_content(self) -> str:
        return """import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
            'border border-input bg-background hover:bg-accent hover:text-accent-foreground': variant === 'outline',
            'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
            'text-primary underline-offset-4 hover:underline': variant === 'link',
          },
          {
            'h-10 px-4 py-2': size === 'default',
            'h-9 rounded-md px-3': size === 'sm',
            'h-11 rounded-md px-8': size === 'lg',
            'h-10 w-10': size === 'icon',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }"""
    
    def _get_utils_content(self) -> str:
        return """import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}"""
    
    def _get_env_example_content(self) -> str:
        return """# Environment variables for {{ project_name }}

# Database
# DATABASE_URL="postgresql://username:password@localhost:5432/database"

# Authentication
# NEXTAUTH_SECRET="your-secret-here"
# NEXTAUTH_URL="http://localhost:3000"

# API Keys
# OPENAI_API_KEY="your-openai-key"
# STRIPE_SECRET_KEY="your-stripe-key"

# Other
# NODE_ENV="development"
"""
