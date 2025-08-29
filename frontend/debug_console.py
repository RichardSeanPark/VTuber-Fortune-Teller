#!/usr/bin/env python3
"""
Debug script to capture console errors and analyze the application state
"""

from playwright.sync_api import sync_playwright
import time
import json

def debug_application():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'])
        context = browser.new_context()
        page = context.new_page()
        
        # Collect console messages
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': f"{msg.location.get('url', '')}:{msg.location.get('line_number', '')}"
        }))
        
        # Collect JavaScript errors
        page.on('pageerror', lambda error: console_messages.append({
            'type': 'pageerror',
            'text': str(error),
            'location': 'page'
        }))
        
        try:
            print("🚀 Loading application and collecting debug info...")
            
            # Navigate to application
            response = page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            print(f"Page response: {response.status}")
            
            # Wait for potential loading
            time.sleep(5)
            
            # Check DOM structure
            dom_info = page.evaluate("""
                () => {
                    const info = {
                        title: document.title,
                        rootElement: !!document.getElementById('root'),
                        live2dElement: !!document.getElementById('live2d-container'),
                        bodyChildren: document.body.children.length,
                        rootChildren: document.getElementById('root') ? document.getElementById('root').children.length : 0,
                        scripts: Array.from(document.scripts).map(s => s.src || 'inline'),
                        stylesheets: Array.from(document.styleSheets).length,
                        canvasElements: document.querySelectorAll('canvas').length,
                        bodyClass: document.body.className,
                        rootClass: document.getElementById('root') ? document.getElementById('root').className : null,
                        computedStyles: {
                            body: window.getComputedStyle(document.body),
                            root: document.getElementById('root') ? window.getComputedStyle(document.getElementById('root')) : null
                        }
                    };
                    
                    // Get background colors
                    info.bodyBgColor = info.computedStyles.body.backgroundColor;
                    info.rootBgColor = info.computedStyles.root ? info.computedStyles.root.backgroundColor : null;
                    
                    return info;
                }
            """)
            
            print("📊 DOM Analysis:")
            print(f"  Title: {dom_info['title']}")
            print(f"  Root element exists: {dom_info['rootElement']}")
            print(f"  Live2D element exists: {dom_info['live2dElement']}")
            print(f"  Body children count: {dom_info['bodyChildren']}")
            print(f"  Root children count: {dom_info['rootChildren']}")
            print(f"  Canvas elements: {dom_info['canvasElements']}")
            print(f"  Body background: {dom_info['bodyBgColor']}")
            print(f"  Root background: {dom_info['rootBgColor']}")
            print(f"  Scripts loaded: {len(dom_info['scripts'])}")
            
            # Check if React is loaded
            react_status = page.evaluate("""
                () => ({
                    react: typeof React !== 'undefined',
                    reactDOM: typeof ReactDOM !== 'undefined',
                    reactDevTools: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
                    viteClient: !!window.__vite_plugin_react_preamble_installed__
                })
            """)
            
            print(f"⚛️ React Status:")
            print(f"  React loaded: {react_status['react']}")
            print(f"  ReactDOM loaded: {react_status['reactDOM']}")
            print(f"  React DevTools: {react_status['reactDevTools']}")
            print(f"  Vite client: {react_status['viteClient']}")
            
            # Check Live2D
            live2d_status = page.evaluate("""
                () => ({
                    live2dCubismCore: typeof Live2DCubismCore !== 'undefined',
                    pixi: typeof PIXI !== 'undefined',
                    live2dPixi: typeof PIXI !== 'undefined' && !!PIXI.live2d,
                    globalLive2D: typeof window.live2dApp !== 'undefined',
                    canvas: document.querySelectorAll('canvas').length
                })
            """)
            
            print(f"🎭 Live2D Status:")
            print(f"  Cubism Core loaded: {live2d_status['live2dCubismCore']}")
            print(f"  PIXI loaded: {live2d_status['pixi']}")
            print(f"  PIXI Live2D: {live2d_status['live2dPixi']}")
            print(f"  Global Live2D app: {live2d_status['globalLive2D']}")
            print(f"  Canvas count: {live2d_status['canvas']}")
            
            # Print console messages
            print(f"\n📝 Console Messages ({len(console_messages)}):")
            for i, msg in enumerate(console_messages):
                print(f"  {i+1}. [{msg['type']}] {msg['text']}")
                if msg['location'] and msg['location'] != ':':
                    print(f"     Location: {msg['location']}")
            
            # Check network requests that might be failing
            print(f"\n🌐 Checking critical resources...")
            
            # Try to detect failed resources
            failed_resources = page.evaluate("""
                () => {
                    const scripts = Array.from(document.scripts);
                    const links = Array.from(document.querySelectorAll('link'));
                    const images = Array.from(document.images);
                    
                    const failed = [];
                    
                    scripts.forEach(script => {
                        if (script.src && !script.src.startsWith('data:')) {
                            // We can't directly check if script failed, but we can note them
                        }
                    });
                    
                    return {
                        totalScripts: scripts.length,
                        totalLinks: links.length,
                        totalImages: images.length
                    };
                }
            """)
            
            print(f"  Scripts: {failed_resources['totalScripts']}")
            print(f"  Links: {failed_resources['totalLinks']}")
            print(f"  Images: {failed_resources['totalImages']}")
            
            # Take a screenshot with DOM overlay
            page.screenshot(path="/home/jhbum01/project/VTuber/project/frontend/screenshots/debug_analysis.png")
            
            print("✅ Debug analysis completed!")
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    debug_application()