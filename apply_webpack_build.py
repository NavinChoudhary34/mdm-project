#!/usr/bin/env python3
"""
Switches the frontend production build from Turbopack (Next.js 16's
new default) back to Webpack, as a test against the Vercel 404 issue.

Usage (run from the project ROOT):
    cd mdm-project-main
    python apply_webpack_build.py

Then commit and push to trigger a fresh Vercel deploy:
    git add frontend/package.json
    git commit -m "Use webpack for production build"
    git push
"""

import os
import shutil
import sys

FILES = {}

FILES['frontend/package.json'] = '{\n  "name": "frontend",\n  "version": "0.1.0",\n  "private": true,\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build --webpack",\n    "start": "next start",\n    "lint": "eslint",\n    "test": "vitest run",\n    "test:watch": "vitest"\n  },\n  "dependencies": {\n    "clsx": "^2.1.1",\n    "date-fns": "^4.4.0",\n    "lucide-react": "^1.31.0",\n    "next": "16.3.1",\n    "react": "19.2.8",\n    "react-dom": "19.2.8"\n  },\n  "devDependencies": {\n    "@tailwindcss/postcss": "^4",\n    "@testing-library/jest-dom": "^7.0.1",\n    "@testing-library/react": "^16.3.2",\n    "@testing-library/user-event": "^14.6.4",\n    "@types/node": "^20",\n    "@types/react": "^19",\n    "@types/react-dom": "^19",\n    "@vitejs/plugin-react": "^6.0.5",\n    "eslint": "^9",\n    "eslint-config-next": "16.3.1",\n    "jsdom": "^30.0.1",\n    "tailwindcss": "^4",\n    "typescript": "^5",\n    "vitest": "^4.1.10"\n  }\n}\n'

def main():
    root = os.getcwd()
    if not os.path.isdir(os.path.join(root, 'backend')) or not os.path.isdir(os.path.join(root, 'frontend')):
        print('Error: run this script from the project root (must contain backend/ and frontend/ folders).')
        sys.exit(1)
    print('Backing up files that will be changed (.bak)...')
    for rel_path in FILES:
        full_path = os.path.join(root, rel_path)
        if os.path.exists(full_path):
            shutil.copyfile(full_path, full_path + '.bak')
    for rel_path, content in FILES.items():
        full_path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f'Writing {rel_path}...')
        with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
    print()
    print('Done. Next: git add frontend/package.json, commit, and push')
    print('to trigger a fresh Vercel deploy using webpack instead of Turbopack.')
    print()
    print('Backups of the original files were saved alongside them as *.bak')

if __name__ == '__main__':
    main()
