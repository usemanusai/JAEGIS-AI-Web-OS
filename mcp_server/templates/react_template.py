"""
React Project Template

Generates React applications with TypeScript and modern tooling.
"""

from typing import Dict, List
from .base_template import BaseTemplate, ProjectStructure, FileTemplate, create_package_json_content, create_gitignore_content, create_readme_content


class ReactTemplate(BaseTemplate):
    """Template for React projects."""
    
    def get_framework_name(self) -> str:
        return "React"
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return React dependencies."""
        return {
            'runtime': [
                'react@latest',
                'react-dom@latest',
                '@types/react@latest',
                '@types/react-dom@latest',
                'typescript@latest'
            ],
            'development': [
                '@vitejs/plugin-react@latest',
                'vite@latest',
                'eslint@latest',
                '@typescript-eslint/eslint-plugin@latest',
                '@typescript-eslint/parser@latest',
                'eslint-plugin-react-hooks@latest',
                'eslint-plugin-react-refresh@latest'
            ]
        }
    
    def get_project_structure(self) -> ProjectStructure:
        """Return React project structure."""
        
        # Dependencies
        deps = self.get_dependencies()
        dependencies = {dep.split('@')[0]: dep.split('@')[1] if '@' in dep else 'latest' 
                       for dep in deps['runtime']}
        dev_dependencies = {dep.split('@')[0]: dep.split('@')[1] if '@' in dep else 'latest' 
                           for dep in deps['development']}
        
        # Scripts
        scripts = {
            "dev": "vite",
            "build": "tsc && vite build",
            "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
            "preview": "vite preview"
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
            
            # Vite config
            FileTemplate(
                path="vite.config.ts",
                content=self._get_vite_config_content()
            ),
            
            # TypeScript config
            FileTemplate(
                path="tsconfig.json",
                content=self._get_tsconfig_content()
            ),
            
            # Index HTML
            FileTemplate(
                path="index.html",
                content=self._get_index_html_content()
            ),
            
            # Main App component
            FileTemplate(
                path="src/App.tsx",
                content=self._get_app_content()
            ),
            
            # Main entry point
            FileTemplate(
                path="src/main.tsx",
                content=self._get_main_content()
            ),
            
            # CSS
            FileTemplate(
                path="src/App.css",
                content=self._get_app_css_content()
            ),
            
            # Index CSS
            FileTemplate(
                path="src/index.css",
                content=self._get_index_css_content()
            ),
            
            # Gitignore
            FileTemplate(
                path=".gitignore",
                content=create_gitignore_content([
                    "# Dependencies",
                    "node_modules/",
                    "",
                    "# Build outputs",
                    "dist/",
                    "build/",
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
                    f"A modern React application built with TypeScript and Vite.",
                    [
                        "Install dependencies: `npm install`",
                        "Start development server: `npm run dev`",
                        "Open http://localhost:5173 in your browser"
                    ]
                ),
                is_template=False
            )
        ]
        
        return ProjectStructure(
            directories=[
                "src",
                "public"
            ],
            files=files,
            dependencies=deps,
            scripts=scripts,
            environment_variables={}
        )
    
    def _get_vite_config_content(self) -> str:
        return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})"""
    
    def _get_tsconfig_content(self) -> str:
        return """{
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
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}"""
    
    def _get_index_html_content(self) -> str:
        return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ project_name }}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""
    
    def _get_app_content(self) -> str:
        return """import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <h1>{{ project_name }}</h1>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
          <p>
            Edit <code>src/App.tsx</code> and save to test HMR
          </p>
        </div>
        <p className="read-the-docs">
          Click on the Vite and React logos to learn more
        </p>
      </div>
    </>
  )
}

export default App"""
    
    def _get_main_content(self) -> str:
        return """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
    
    def _get_app_css_content(self) -> str:
        return """#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.card {
  padding: 2em;
}

.read-the-docs {
  color: #888;
}"""
    
    def _get_index_css_content(self) -> str:
        return """:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

a {
  font-weight: 500;
  color: #646cff;
  text-decoration: inherit;
}
a:hover {
  color: #535bf2;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

h1 {
  font-size: 3.2em;
  line-height: 1.1;
}

button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  background-color: #1a1a1a;
  color: inherit;
  cursor: pointer;
  transition: border-color 0.25s;
}
button:hover {
  border-color: #646cff;
}
button:focus,
button:focus-visible {
  outline: 4px auto -webkit-focus-ring-color;
}

@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
  a:hover {
    color: #747bff;
  }
  button {
    background-color: #f9f9f9;
  }
}"""
