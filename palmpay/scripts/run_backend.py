"""Launch the FastAPI backend with uvicorn."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for p in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / "src" / "xrtech", PROJECT_ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import uvicorn  # noqa: E402

from backend.settings import API_PORT  # noqa: E402
from network_urls import get_lan_ipv4, print_urls  # noqa: E402

if __name__ == "__main__":
    bind_host = "0.0.0.0"
    lan = get_lan_ipv4()
    print(f"Starting backend on {bind_host}:{API_PORT}")
    if lan:
        print(f"Phone API URL: http://{lan}:{API_PORT}/api/palmpay/health")
    print_urls(backend_port=API_PORT)
    uvicorn.run(
        "backend.main:app",
        host=bind_host,
        port=API_PORT,
        reload=False,
        log_level="info",
    )
