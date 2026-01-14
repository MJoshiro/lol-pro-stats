import sys
import os
import threading

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_flask_in_thread(app, port=5000):
    """Run Flask app in a background thread."""
    app.run(host='127.0.0.1', port=port, threaded=True, use_reloader=False)


def main():
    """Main entry point for the application."""
    print("=" * 50)
    print("LoL Pro Player Stats System")
    print("=" * 50)
    
    # Import here to avoid issues with path
    import webview
    from web.app import create_app
    
    # Create Flask app
    print("\n[1/3] Initializing application...")
    app = create_app()
    
    # Print registered routes for debugging
    print("\nRegistered API routes:")
    for rule in app.url_map.iter_rules():
        if 'api' in rule.rule:
            print(f"  {rule.methods} {rule.rule}")
    
    # Start Flask in background thread
    print("\n[2/3] Starting web server...")
    port = 5000
    server_thread = threading.Thread(
        target=run_flask_in_thread,
        args=(app, port),
        daemon=True
    )
    server_thread.start()
    
    # Give server time to start
    import time
    time.sleep(0.5)
    
    # Create PyWebView window
    print("[3/3] Opening application window...")
    print("\nApplication is running. Close the window to exit.\n")
    
    window = webview.create_window(
        title="LoL Pro Player Stats",
        url=f"http://127.0.0.1:{port}",
        width=1200,
        height=800,
        min_size=(1000, 650),
        resizable=True,
        text_select=True
    )
    
    # Start PyWebView (this blocks until window is closed)
    webview.start()
    
    print("\nApplication closed. Goodbye!")


def run_browser_mode():
    """
    Alternative: Run in browser mode (for development/debugging).
    
    Usage:
        python main.py --browser
    """
    from web.app import create_app
    
    print("=" * 50)
    print("LoL Pro Player Stats System")
    print("Running in BROWSER MODE")
    print("=" * 50)
    print("\nOpen http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop the server\n")
    
    app = create_app()
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    # Check for browser mode flag
    if len(sys.argv) > 1 and sys.argv[1] == '--browser':
        run_browser_mode()
    else:
        main()
