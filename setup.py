from pathlib import Path

from setuptools import find_packages, setup


def find_version() -> str:
    version = "0.0.2"
    extension_yaml_path = Path(__file__).parent / "extension" / "extension.yaml"

    try:
        with extension_yaml_path.open(encoding="utf-8") as extension_yaml:
            for line in extension_yaml:
                if line.startswith("version:"):
                    return line.split(":", 1)[1].strip().strip('"')
    except OSError:
        pass

    return version


setup(
    name="custom_huawei_campusinsight",
    version=find_version(),
    description="Dynatrace extension for Huawei CampusInsight",
    author="Core Consulting",
    packages=find_packages(),
    python_requires=">=3.10",
    include_package_data=True,
    install_requires=["dt-extensions-sdk>=1.8.0"],
    extras_require={"dev": ["dt-extensions-sdk[cli]"]},
)
