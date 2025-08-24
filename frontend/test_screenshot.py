#!/usr/bin/env python3
"""
Live2D + React Application Testing Script
Takes screenshots and checks functionality of the integrated application
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_application():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        try:
            print("🚀 Accessing the application...")
            
            # Navigate to the application
            page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            
            # Wait for page to load
            time.sleep(3)
            
            # Take initial screenshot
            print("📸 Taking initial screenshot...")
            page.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/initial_load.png", full_page=True)
            
            # Check if React interface elements are visible
            print("🔍 Checking React interface elements...")
            
            # Check for main containers
            react_container = page.query_selector('[class*="App"]') or page.query_selector('div[id="root"]')
            live2d_container = page.query_selector('[id*="live2d"]') or page.query_selector('[class*="live2d"]') or page.query_selector('canvas')
            
            print(f"React container found: {react_container is not None}")
            print(f"Live2D container found: {live2d_container is not None}")
            
            # Try to find fortune-telling interface elements
            fortune_elements = page.query_selector_all('button, input, form, [class*="fortune"], [class*="chat"]')
            print(f"Fortune interface elements found: {len(fortune_elements)}")
            
            # Try to find canvas elements (Live2D likely uses canvas)
            canvas_elements = page.query_selector_all('canvas')
            print(f"Canvas elements found: {len(canvas_elements)}")
            
            # Check for WebGL context (Live2D uses WebGL)
            webgl_support = page.evaluate("""
                () => {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    return gl !== null;
                }
            """)
            print(f"WebGL support: {webgl_support}")
            
            # Take screenshot of specific areas if possible
            if live2d_container:
                print("📸 Taking Live2D container screenshot...")
                live2d_container.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/live2d_area.png")
            
            # Try to interact with the interface
            print("🖱️ Testing interactions...")
            
            # Look for clickable elements
            clickable_elements = page.query_selector_all('button:visible, [role="button"]:visible, input:visible')
            print(f"Clickable elements found: {len(clickable_elements)}")
            
            if clickable_elements:
                # Try clicking the first button
                try:
                    clickable_elements[0].click()
                    time.sleep(2)
                    page.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/after_click.png", full_page=True)
                    print("✅ Successfully clicked first interactive element")
                except Exception as e:
                    print(f"❌ Failed to click element: {e}")
            
            # Test mouse movement for Live2D tracking
            print("🖱️ Testing mouse movement for Live2D tracking...")
            
            # Get viewport center
            viewport_size = page.viewport_size
            center_x = viewport_size['width'] // 2
            center_y = viewport_size['height'] // 2
            
            # Move mouse in a pattern and take screenshots
            positions = [
                (center_x - 200, center_y - 200),  # Top left
                (center_x + 200, center_y - 200),  # Top right
                (center_x + 200, center_y + 200),  # Bottom right
                (center_x - 200, center_y + 200),  # Bottom left
                (center_x, center_y)               # Center
            ]
            
            for i, (x, y) in enumerate(positions):
                page.mouse.move(x, y)
                time.sleep(1)
                page.screenshot(path=f"/home/jhbum01/project/VTuber/project/frontend/screenshots/mouse_position_{i}.png", full_page=True)
            
            # Check console for errors
            print("📊 Checking console for errors...")
            console_messages = []
            
            def handle_console(msg):
                console_messages.append({
                    'type': msg.type,
                    'text': msg.text
                })
            
            page.on('console', handle_console)
            
            # Wait a bit to collect console messages
            time.sleep(2)
            
            # Print console messages
            for msg in console_messages[-10:]:  # Last 10 messages
                print(f"Console {msg['type']}: {msg['text']}")
            
            # Check network requests
            print("🌐 Checking network activity...")
            
            # Reload page to capture network requests
            response = page.goto("http://localhost:3000", wait_until="networkidle")
            print(f"Main page response status: {response.status}")
            
            # Take final comprehensive screenshot
            print("📸 Taking final comprehensive screenshot...")
            page.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/final_state.png", full_page=True)
            
            # Get page title and URL
            title = page.title()
            url = page.url
            print(f"Page title: {title}")
            print(f"Current URL: {url}")
            
            # Get page dimensions
            dimensions = page.evaluate("""
                () => ({
                    window: { width: window.innerWidth, height: window.innerHeight },
                    document: { width: document.body.scrollWidth, height: document.body.scrollHeight }
                })
            """)
            print(f"Page dimensions: {dimensions}")
            
            print("✅ Testing completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            # Take error screenshot
            try:
                page.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/error_state.png", full_page=True)
            except:
                pass
        
        finally:
            browser.close()

if __name__ == "__main__":
    # Create screenshots directory
    import os
    os.makedirs("/home/jhbum01/project/VTuber/project/frontend/screenshots", exist_ok=True)
    test_application()