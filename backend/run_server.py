#!/usr/bin/env python3
"""
Fortune VTuber Backend Server Runner

Simple script to start the Fortune VTuber backend server.
Based on Open-LLM-VTuber's run_server.py pattern.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fortune_vtuber.main import run_dev_server, run_production_server
from fortune_vtuber.config.settings import get_settings, print_current_settings


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fortune VTuber Backend Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_server.py                    # Start development server
  python run_server.py --production       # Start production server
  python run_server.py --host 0.0.0.0     # Bind to all interfaces
  python run_server.py --port 8080        # Use port 8080
  python run_server.py --verbose          # Show current settings
        """
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to (overrides config)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to (overrides config)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show current settings before starting"
    )
    
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Environment file to load (default: .env)"
    )
    
    return parser.parse_args()


def setup_environment(args):
    """Setup environment variables"""
    env_file = Path(args.env_file)
    
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        # Explicitly load .env file using python-dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            print(f"✅ Environment variables loaded from {env_file}")
            
            # Verify critical environment variables are loaded
            cerebras_key = os.environ.get("CEREBRAS_API_KEY")
            if cerebras_key:
                print(f"✅ CEREBRAS_API_KEY loaded: {cerebras_key[:10]}...{cerebras_key[-4:]}")
            else:
                print("⚠️ CEREBRAS_API_KEY not found in environment")
                
        except ImportError:
            print("⚠️ python-dotenv not available, using pydantic-settings fallback")
        except Exception as e:
            print(f"❌ Failed to load .env file: {e}")
    else:
        print(f"Environment file not found: {env_file}")
        if args.env_file != ".env":
            print("Creating default .env file...")
            create_default_env_file()
    
    # Override settings from command line
    if args.host:
        os.environ["FORTUNE_SERVER_HOST"] = args.host
    
    if args.port:
        os.environ["FORTUNE_SERVER_PORT"] = str(args.port)
    
    if args.production:
        os.environ["FORTUNE_ENVIRONMENT"] = "production"
        os.environ["FORTUNE_SERVER_DEBUG"] = "false"
        os.environ["FORTUNE_SERVER_RELOAD"] = "false"


def create_default_env_file():
    """Create default .env file from .env.example"""
    example_file = Path(".env.example")
    env_file = Path(".env")
    
    if example_file.exists():
        try:
            with open(example_file, 'r') as src:
                content = src.read()
            
            with open(env_file, 'w') as dst:
                dst.write(content)
            
            print(f"Created default .env file from {example_file}")
        except Exception as e:
            print(f"Failed to create .env file: {e}")
    else:
        print("No .env.example file found to copy from")


def check_prerequisites():
    """Check if all prerequisites are met"""
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required, found {sys.version}")
    
    # Check if in virtual environment (recommended)
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not running in a virtual environment (recommended)")
    
    # Check required directories
    required_dirs = ["logs", "static", "data", "cache"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                errors.append(f"Failed to create directory {dir_path}: {e}")
    
    if errors:
        print("Prerequisites check failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


def main():
    """Main entry point"""
    print("Fortune VTuber Backend Server")
    print("=" * 50)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup environment
    setup_environment(args)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    try:
        # Load settings to validate configuration
        settings = get_settings()
        
        # Show current settings if requested
        if args.verbose:
            print("\nCurrent Configuration:")
            print("-" * 30)
            print_current_settings()
            print()
        
        # Start appropriate server
        if settings.is_production() or args.production:
            print(f"Starting production server on {settings.server.host}:{settings.server.port}")
            run_production_server()
        else:
            print(f"Starting development server on {settings.server.host}:{settings.server.port}")
            print(f"Environment: {settings.environment}")
            print(f"Debug mode: {settings.server.debug}")
            print(f"Auto-reload: {settings.server.reload}")
            print(f"Database: {settings.get_database_url().split('?')[0]}")
            print()
            run_dev_server()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nFailed to start server: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()