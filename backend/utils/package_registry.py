"""Package Registry Utilities

Fetch latest package versions from npm (Node.js) and PyPI (Python) registries.
"""

import requests
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PackageRegistry:
    """Fetch package information from npm and PyPI registries."""

    NPM_REGISTRY = "https://registry.npmjs.org"
    PYPI_API = "https://pypi.org/pypi"

    @staticmethod
    def get_npm_latest_version(package_name: str) -> Optional[str]:
        """Get latest version of an npm package.

        Args:
            package_name: Name of the npm package

        Returns:
            Latest version string or None if fetch fails
        """
        try:
            url = f"{PackageRegistry.NPM_REGISTRY}/{package_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get("dist-tags", {}).get("latest")

            logger.info("npm_version_fetched",
                       package=package_name,
                       latest=latest_version)

            return latest_version

        except requests.exceptions.RequestException as e:
            logger.warning("npm_fetch_failed",
                          package=package_name,
                          error=str(e))
            return None

        except Exception as e:
            logger.error("npm_fetch_error",
                        package=package_name,
                        error=str(e))
            return None

    @staticmethod
    def get_pypi_latest_version(package_name: str) -> Optional[str]:
        """Get latest version of a PyPI package.

        Args:
            package_name: Name of the PyPI package

        Returns:
            Latest version string or None if fetch fails
        """
        try:
            url = f"{PackageRegistry.PYPI_API}/{package_name}/json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get("info", {}).get("version")

            logger.info("pypi_version_fetched",
                       package=package_name,
                       latest=latest_version)

            return latest_version

        except requests.exceptions.RequestException as e:
            logger.warning("pypi_fetch_failed",
                          package=package_name,
                          error=str(e))
            return None

        except Exception as e:
            logger.error("pypi_fetch_error",
                        package=package_name,
                        error=str(e))
            return None

    @staticmethod
    def enrich_dependencies_with_latest(dependencies: Dict, project_type: str) -> Dict:
        """Enrich dependency dict with latest versions from registry.

        Args:
            dependencies: Dict of {package_name: current_version}
            project_type: "nodejs" or "python"

        Returns:
            Enriched dict with latest_version field added
        """
        enriched = {}

        for package_name, current_version in dependencies.items():
            # Fetch latest version
            if project_type == "nodejs":
                latest = PackageRegistry.get_npm_latest_version(package_name)
            elif project_type == "python":
                latest = PackageRegistry.get_pypi_latest_version(package_name)
            else:
                latest = None

            enriched[package_name] = {
                "current_version": current_version,
                "latest_version": latest if latest else "unknown"
            }

            logger.info("dependency_enriched",
                       package=package_name,
                       current=current_version,
                       latest=latest if latest else "unknown")

        return enriched


# CLI test
if __name__ == "__main__":
    print("=" * 80)
    print("PACKAGE REGISTRY UTILITY - TEST")
    print("=" * 80)

    # Test npm packages
    print("\n1. Testing npm packages:")
    npm_packages = ["express", "cors", "dotenv", "body-parser", "morgan"]

    for pkg in npm_packages:
        version = PackageRegistry.get_npm_latest_version(pkg)
        print(f"   {pkg}: {version}")

    # Test PyPI packages
    print("\n2. Testing PyPI packages:")
    pypi_packages = ["flask", "requests", "django"]

    for pkg in pypi_packages:
        version = PackageRegistry.get_pypi_latest_version(pkg)
        print(f"   {pkg}: {version}")

    # Test enrichment
    print("\n3. Testing dependency enrichment:")
    deps = {
        "express": "4.16.0",
        "cors": "2.8.4",
        "dotenv": "6.0.0"
    }

    enriched = PackageRegistry.enrich_dependencies_with_latest(deps, "nodejs")
    import json
    print(json.dumps(enriched, indent=2))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
