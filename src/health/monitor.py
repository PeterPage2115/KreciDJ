"""Health monitoring system for Discord Music Bot"""

import asyncio
import json
import time
import psutil
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import os
import sys

logger = logging.getLogger('discord_bot')

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.handle_health_check()
        elif self.path == '/metrics':
            self.handle_metrics()
        elif self.path == '/status':
            self.handle_status()
        else:
            self.send_error(404)
    
    def handle_health_check(self):
        """Basic health check endpoint"""
        try:
            status = self.get_health_status()
            response_code = 200 if status['healthy'] else 503
            
            self.send_response(response_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            response = json.dumps(status, indent=2)
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_error(500, f"Health check failed: {e}")
    
    def handle_metrics(self):
        """Detailed metrics endpoint"""
        try:
            metrics = self.get_detailed_metrics()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = json.dumps(metrics, indent=2)
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_error(500, f"Metrics failed: {e}")
    
    def handle_status(self):
        """Simple status endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")
    
    def get_bot_instance(self):
        """Safely get bot instance to avoid circular imports"""
        try:
            # Try to get bot from global scope if available
            import builtins
            if hasattr(builtins, '_bot_instance'):
                return getattr(builtins, '_bot_instance')
            
            # Alternative: try to import from bot module
            try:
                # Add parent directory to path temporarily
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                import bot
                return getattr(bot, 'bot', None)
            except (ImportError, AttributeError):
                return None
                
        except Exception:
            return None
    
    def get_health_status(self):
        """Get basic health status"""
        try:
            bot_instance = self.get_bot_instance()
            bot_ready = False
            
            if bot_instance:
                bot_ready = hasattr(bot_instance, 'is_ready') and bot_instance.is_ready()
            
            return {
                "healthy": bot_ready,
                "timestamp": int(time.time()),
                "service": "discord-music-bot",
                "version": "1.0.0",
                "bot_connected": bot_instance is not None
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": int(time.time()),
                "bot_connected": False
            }
    
    def get_detailed_metrics(self):
        """Get detailed system metrics"""
        try:
            # Process info
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Bot info
            bot_info = {"status": "not_available"}
            bot_instance = self.get_bot_instance()
            
            if bot_instance and hasattr(bot_instance, 'is_ready') and bot_instance.is_ready():
                try:
                    bot_info = {
                        "status": "ready",
                        "guilds": len(bot_instance.guilds),
                        "voice_clients": len(bot_instance.voice_clients),
                        "commands_executed": getattr(bot_instance, 'commands_executed', 0),
                        "uptime_seconds": int((datetime.utcnow() - getattr(bot_instance, 'start_time', datetime.utcnow())).total_seconds())
                    }
                except Exception as e:
                    bot_info = {"status": "error", "error": str(e)}
            
            return {
                "timestamp": int(time.time()),
                "system": {
                    "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads(),
                    "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
                },
                "bot": bot_info,
                "healthy": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "healthy": False,
                "timestamp": int(time.time())
            }
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

class HealthMonitor:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
        self.bot_instance = None
    
    def set_bot_instance(self, bot):
        """Set bot instance for monitoring"""
        self.bot_instance = bot
        # Store in global scope for health handler access
        import builtins
        setattr(builtins, '_bot_instance', bot)
    
    def start(self):
        """Start health monitoring server"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Health monitor started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start health monitor: {e}")
            return False
    
    def stop(self):
        """Stop health monitoring server"""
        if self.server:
            self.server.shutdown()
            logger.info("Health monitor stopped")
        
        # Clean up global bot instance
        try:
            import builtins
            if hasattr(builtins, '_bot_instance'):
                delattr(builtins, '_bot_instance')
        except:
            pass

# Global instance
health_monitor = HealthMonitor()