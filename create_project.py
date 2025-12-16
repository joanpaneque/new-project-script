#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Ask for the project name
project_name = input("Project name: ")

# Execute composer global require laravel/installer
print("Installing Laravel installer...")
subprocess.run(["composer", "global", "require", "laravel/installer"], check=True)
print("Laravel installer installed successfully")

# Execute laravel new with the project name
print(f"Creating Laravel project '{project_name}'...")
os.chdir(script_dir)
subprocess.run(f"laravel new {project_name} --pest --boost --npm --no-interaction", shell=True, check=True)
print(f"Laravel project '{project_name}' created successfully")

# Change to project directory
project_path = script_dir / project_name
os.chdir(project_path)

# Install Laravel Sail
print("Installing Laravel Sail...")
subprocess.run(["composer", "require", "laravel/sail", "--dev"], check=True)
print("Laravel Sail installed successfully")

# Create docker-compose.yml with PostgreSQL
print("Creating docker-compose.yml with PostgreSQL...")
docker_compose_content = """version: '3.8'

services:
    laravel.test:
        build:
            context: ./vendor/laravel/sail/runtimes/8.4
            dockerfile: Dockerfile
            args:
                WWWGROUP: '${WWWGROUP}'
        image: sail-8.4/app
        extra_hosts:
            - 'host.docker.internal:host-gateway'
        ports:
            - '${APP_PORT:-80}:80'
            - '${VITE_PORT:-5173}:5173'
        environment:
            WWWUSER: '${WWWUSER}'
            LARAVEL_SAIL: 1
            XDEBUG_MODE: '${XDEBUG_MODE:-off}'
            XDEBUG_CONFIG: '${XDEBUG_CONFIG:-client_host=host.docker.internal}'
        volumes:
            - '.:/var/www/html'
        networks:
            - sail
        depends_on:
            - pgsql
            - redis

    pgsql:
        image: 'postgres:15'
        environment:
            PGPASSWORD: '${DB_PASSWORD:-password}'
            POSTGRES_DB: '${DB_DATABASE:-laravel}'
            POSTGRES_USER: '${DB_USERNAME:-sail}'
            POSTGRES_PASSWORD: '${DB_PASSWORD:-password}'
            POSTGRES_HOST_AUTH_METHOD: 'trust'
        ports:
            - '${FORWARD_DB_PORT:-5432}:5432'
        volumes:
            - 'sailpgsql:/var/lib/postgresql/data'
        networks:
            - sail
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME:-sail}"]
            retries: 3
            timeout: 5s

    redis:
        image: 'redis:alpine'
        ports:
            - '${FORWARD_REDIS_PORT:-6379}:6379'
        volumes:
            - 'sailredis:/data'
        networks:
            - sail
        healthcheck:
            test: ["CMD", "redis-cli", "ping"]
            retries: 3
            timeout: 5s

networks:
    sail:
        driver: bridge

volumes:
    sailpgsql:
        driver: local
    sailredis:
        driver: local
"""

with open("docker-compose.yml", "w") as f:
    f.write(docker_compose_content)
print("docker-compose.yml created successfully")

# Update .env file with PostgreSQL configuration
print("Updating .env file with PostgreSQL configuration...")
env_file = Path(".env")
if env_file.exists():
    with open(env_file, "r") as f:
        lines = f.readlines()
    
    updated_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip DB_CONNECTION - keep it as is (already uncommented)
        if stripped.startswith("DB_CONNECTION"):
            # Update DB_CONNECTION to pgsql if needed
            if "=mysql" in stripped or "=sqlite" in stripped:
                updated_lines.append("DB_CONNECTION=pgsql\n")
            else:
                updated_lines.append(line)
        # Uncomment and update other DB_ variables (handle #DB_ or # DB_)
        elif stripped.startswith("#") and "DB_HOST" in stripped:
            updated_lines.append("DB_HOST=pgsql\n")
        elif stripped.startswith("#") and "DB_PORT" in stripped:
            updated_lines.append("DB_PORT=5432\n")
        elif stripped.startswith("#") and "DB_DATABASE" in stripped:
            updated_lines.append("DB_DATABASE=laravel\n")
        elif stripped.startswith("#") and "DB_USERNAME" in stripped:
            updated_lines.append("DB_USERNAME=sail\n")
        elif stripped.startswith("#") and "DB_PASSWORD" in stripped:
            updated_lines.append("DB_PASSWORD=password\n")
        # Update existing uncommented DB_ variables
        elif stripped.startswith("DB_HOST="):
            updated_lines.append("DB_HOST=pgsql\n")
        elif stripped.startswith("DB_PORT="):
            updated_lines.append("DB_PORT=5432\n")
        elif stripped.startswith("DB_DATABASE="):
            updated_lines.append("DB_DATABASE=laravel\n")
        elif stripped.startswith("DB_USERNAME="):
            updated_lines.append("DB_USERNAME=sail\n")
        elif stripped.startswith("DB_PASSWORD="):
            updated_lines.append("DB_PASSWORD=password\n")
        else:
            updated_lines.append(line)
    
    with open(env_file, "w") as f:
        f.writelines(updated_lines)
    print(".env file updated successfully")
else:
    print("Warning: .env file not found")

# Start Sail containers
print("Starting Sail containers...")
subprocess.run(["./vendor/bin/sail", "up", "-d"], check=True)
print("Sail containers started successfully")

# Run migrations
print("Running database migrations...")
subprocess.run(["./vendor/bin/sail", "artisan", "migrate"], check=True)
print("Database migrations completed successfully")

# Update composer.json to replace "php artisan" with "./vendor/bin/sail artisan"
print("Updating composer.json scripts...")
composer_file = Path("composer.json")
if composer_file.exists():
    with open(composer_file, "r") as f:
        composer_content = f.read()
    
    composer_content = composer_content.replace("php artisan", "./vendor/bin/sail artisan")
    
    with open(composer_file, "w") as f:
        f.write(composer_content)
    print("composer.json updated successfully")
else:
    print("Warning: composer.json file not found")

# Install Inertia.js Laravel adapter
print("Installing Inertia.js Laravel adapter...")
subprocess.run(["./vendor/bin/sail", "composer", "require", "inertiajs/inertia-laravel"], check=True)
print("Inertia.js Laravel adapter installed successfully")

# Install Vue and Vue plugin for Vite
print("Installing Vue and dependencies...")
subprocess.run(["./vendor/bin/sail", "npm", "install", "vue", "@vitejs/plugin-vue", "@inertiajs/vue3"], check=True)
print("Vue and dependencies installed successfully")

# Install Tailwind CSS 4
print("Installing Tailwind CSS 4...")
subprocess.run(["./vendor/bin/sail", "npm", "install", "-D", "tailwindcss", "@tailwindcss/vite"], check=True)
print("Tailwind CSS 4 installed successfully")

# Update resources/css/app.css with Tailwind CSS 4 configuration
print("Updating resources/css/app.css...")
app_css_content = """@import "tailwindcss";

@source '../../vendor/laravel/framework/src/Illuminate/Pagination/resources/views/*.blade.php';
@source '../../storage/framework/views/*.php';
@source '../**/*.blade.php';
@source '../**/*.js';
"""
app_css = Path("resources/css/app.css")
if app_css.exists():
    with open(app_css, "w") as f:
        f.write(app_css_content)
    print("resources/css/app.css updated successfully")
else:
    Path("resources/css").mkdir(parents=True, exist_ok=True)
    with open(app_css, "w") as f:
        f.write(app_css_content)
    print("resources/css/app.css created successfully")

# Update vite.config.js to include Vue plugin
print("Updating vite.config.js...")
vite_config = Path("vite.config.js")
if vite_config.exists():
    with open(vite_config, "r") as f:
        vite_content = f.read()
    
    # Check if vue plugin is already imported
    if "import vue from '@vitejs/plugin-vue'" not in vite_content:
        # Add vue import after laravel import
        vite_content = vite_content.replace(
            "import laravel from 'laravel-vite-plugin';",
            "import laravel from 'laravel-vite-plugin';\nimport vue from '@vitejs/plugin-vue';"
        )
        
        # Add vue plugin to plugins array
        if "vue({" not in vite_content:
            vite_content = vite_content.replace(
                "        laravel({",
                "        vue({\n            template: {\n                transformAssetUrls: {\n                    base: null,\n                    includeAbsolute: false,\n                },\n            },\n        }),\n        laravel({"
            )
    
    with open(vite_config, "w") as f:
        f.write(vite_content)
    print("vite.config.js updated successfully")
else:
    print("Warning: vite.config.js file not found")

# Delete all files in resources/views and create app.blade.php
print("Setting up Inertia views...")
views_dir = Path("resources/views")
if views_dir.exists():
    # Delete all files in resources/views
    for file in views_dir.iterdir():
        if file.is_file():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(file)
else:
    views_dir.mkdir(parents=True, exist_ok=True)

app_blade_content = """<html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1">
        @vite(['resources/css/app.css', 'resources/js/app.js'])
        @inertiaHead
    </head>
    <body>
        @inertia
    </body>
</html>
"""

with open("resources/views/app.blade.php", "w") as f:
    f.write(app_blade_content)
print("app.blade.php created successfully")

# Execute inertia:middleware command
print("Installing Inertia middleware...")
subprocess.run(["./vendor/bin/sail", "artisan", "inertia:middleware"], check=True)
print("Inertia middleware installed successfully")

# Delete and recreate bootstrap/app.php
print("Updating bootstrap/app.php...")
bootstrap_app = Path("bootstrap/app.php")
if bootstrap_app.exists():
    bootstrap_app.unlink()

bootstrap_app_content = """<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use App\Http\Middleware\HandleInertiaRequests;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->web(append: [
            HandleInertiaRequests::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        //
    })->create();
"""

with open("bootstrap/app.php", "w") as f:
    f.write(bootstrap_app_content)
print("bootstrap/app.php updated successfully")

# Delete and recreate resources/js/app.js
print("Updating resources/js/app.js...")
app_js = Path("resources/js/app.js")
if app_js.exists():
    app_js.unlink()

app_js_content = """import { createApp, h } from 'vue'
import { createInertiaApp } from '@inertiajs/vue3'

createInertiaApp({
    resolve: name => {
        const pages = import.meta.glob('./Pages/**/*.vue', { eager: true })
        return pages[`./Pages/${name}.vue`]
    },
    setup({ el, App, props, plugin }) {
        createApp({ render: () => h(App, props) })
            .use(plugin)
            .mount(el)
    },
})
"""

with open("resources/js/app.js", "w") as f:
    f.write(app_js_content)
print("resources/js/app.js updated successfully")

# Delete and recreate routes/web.php
print("Updating routes/web.php...")
web_routes = Path("routes/web.php")
if web_routes.exists():
    web_routes.unlink()

web_routes_content = """<?php

use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('Welcome');
});
"""

with open("routes/web.php", "w") as f:
    f.write(web_routes_content)
print("routes/web.php updated successfully")

# Create directories
print("Creating directories...")
Path("resources/js/Pages").mkdir(parents=True, exist_ok=True)
Path("resources/js/Components").mkdir(parents=True, exist_ok=True)
Path("resources/js/Layouts").mkdir(parents=True, exist_ok=True)
print("Directories created successfully")

# Create Welcome.vue
print("Creating Welcome.vue...")
welcome_vue_content = """<script setup>


</script>

<template>
    <div>
        <h1>Test</h1>
    </div>
</template>
"""

with open("resources/js/Pages/Welcome.vue", "w") as f:
    f.write(welcome_vue_content)
print("Welcome.vue created successfully")

print(f"\nSetup complete! Your Laravel project '{project_name}' is ready.")

