import os
import time
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOTS_DIR = r"c:\Users\hp\Documents\ENSAM\S8\ZZ PROJET METIERS\Get Rich or Die Tryin\screenshots"

ROLES_PAGES = {
    "admin": {
        "credentials": ("admin", "123"),
        "folder": "screen_admin",
        "pages": {
            "dashboard": "/admin/dashboard/",
            "users": "/admin/users/",
            "companies": "/admin/companies/",
            "transporters": "/admin/transporters/",
            "chauffeurs": "/admin/chauffeurs/",
            "zones": "/admin/zones/",
            "missions": "/admin/missions/",
            "hubs": "/admin/hubs/",
            "warehouse": "/admin/warehouse/",
            "flux": "/admin/flux/",
            "orders": "/admin/orders/",
            "monitoring": "/admin/monitoring/",
            "analytics": "/admin/analytics/",
            "settings": "/admin/settings/"
        }
    },
    "entreprise": {
        "credentials": ("ecolife_ma", "123"),
        "folder": "screen_chauffeur", # Wait, user requested screen_admin, screen_chauffeur ... let's name folders appropriately
        "folder_override": "screen_entreprise",
        "pages": {
            "dashboard": "/enterprise/dashboard/",
            "products": "/enterprise/products/",
            "orders": "/enterprise/orders/",
            "carbon": "/enterprise/carbon/"
        }
    },
    "chauffeur": {
        "credentials": ("driver_ahmed", "123"),
        "folder": "screen_chauffeur",
        "pages": {
            "dashboard": "/transporter/",
            "historique": "/transporter/historique/",
            "notifications": "/transporter/notifications/"
        }
    },
    "client": {
        "credentials": ("youssef_alami", "123"),
        "folder": "screen_client",
        "pages": {
            "marketplace": "/client/marketplace/",
            "impact_eco": "/client/impact-eco/",
            "orders": "/client/orders/"
        }
    }
}

async def take_screenshots():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        
        # We want to create directories first
        for role, info in ROLES_PAGES.items():
            folder_name = info.get("folder_override", info["folder"])
            path = os.path.join(SCREENSHOTS_DIR, folder_name)
            os.makedirs(path, exist_ok=True)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        # Let's take screenshot of the login page first
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        print("Visiting login page...")
        try:
            response = await page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
            print(f"Login page response status: {response.status if response else 'No response'}")
            # Wait a bit for transition
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "login.png"))
            print("Saved login.png")
        except Exception as e:
            print(f"Error screenshotting login page: {e}")
        await context.close()
        
        results = []
        
        for role, info in ROLES_PAGES.items():
            print(f"\n--- Testing role: {role} ---")
            context = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await context.new_page()
            
            # Go to login page
            await page.goto(f"{BASE_URL}/login/")
            
            # Fill credentials
            username, password = info["credentials"]
            await page.fill("#username", username)
            await page.fill("#password", password)
            
            # Click submit
            print(f"Logging in as {username}...")
            async with page.expect_navigation(wait_until="networkidle"):
                await page.click('button[type="submit"]')
            
            # Check redirect URL to verify successful login
            current_url = page.url
            print(f"Logged in. Redirected to: {current_url}")
            
            folder_name = info.get("folder_override", info["folder"])
            
            # Visit all pages for this role
            for name, path_suffix in info["pages"].items():
                target_url = f"{BASE_URL}{path_suffix}"
                print(f"Visiting {target_url}...")
                try:
                    response = await page.goto(target_url, wait_until="load")
                    # Wait extra time for animations, Leaflet map load, or Chart.js charts
                    await page.wait_for_timeout(2500)
                    
                    status = response.status if response else "Unknown"
                    print(f"  Response status: {status}")
                    
                    # Take screenshot
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, folder_name, f"{name}.png")
                    await page.screenshot(path=screenshot_path)
                    print(f"  Saved screenshot: {screenshot_path}")
                    
                    # Store result
                    results.append({
                        "role": role,
                        "page_name": name,
                        "url": target_url,
                        "status": status,
                        "ok": status == 200,
                        "error": None
                    })
                except Exception as e:
                    print(f"  Error visiting {target_url}: {e}")
                    results.append({
                        "role": role,
                        "page_name": name,
                        "url": target_url,
                        "status": "ERROR",
                        "ok": False,
                        "error": str(e)
                    })
            
            # Logout
            print(f"Logging out {username}...")
            await page.goto(f"{BASE_URL}/logout/")
            await page.wait_for_timeout(1000)
            await context.close()
            
        await browser.close()
        
        # Print summary
        print("\n=== SCREENSHOTS & HEALTH CHECK SUMMARY ===")
        all_ok = True
        for res in results:
            status_str = "OK" if res["ok"] else f"FAILED ({res['status']}: {res['error']})"
            print(f"[{res['role'].upper()}] {res['page_name']}: {status_str}")
            if not res["ok"]:
                all_ok = False
        
        if all_ok:
            print("\nAll tested pages are functional (status code 200)!")
        else:
            print("\nSome pages failed to load correctly!")

if __name__ == "__main__":
    asyncio.run(take_screenshots())
